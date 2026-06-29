"""Tenant-scoped patient CRUD."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.tenant.limits import assert_trial_patient_capacity
from app.domains.patients.repositories.patient_allergy_repository import PatientAllergyRepository
from app.domains.patients.repositories.patient_contact_repository import PatientContactRepository
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.patients.repositories.visit_history_repository import PatientVisitHistoryRepository
from app.domains.patients.schemas.allergy import AllergyCreateRequest, AllergyResponse
from app.domains.patients.schemas.chronic_condition import (
    ChronicConditionCreateRequest,
    ChronicConditionResponse,
)
from app.domains.patients.schemas.duplicate import DuplicateCheckResponse, DuplicateMatchResponse
from app.domains.patients.schemas.contact import ContactCreateRequest, ContactResponse
from app.domains.patients.schemas.patient import (
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListItem,
    PatientUpdateRequest,
)
from app.domains.patients.schemas.visit_history import PatientVisitHistoryItem
from app.domains.platform.repositories.location_repository import LocationRepository
from app.models.core.patient import Patient


class PatientService:
    """CRUD for patient records — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = PatientRepository(db, tenant_id)
        self._allergy_repo = PatientAllergyRepository(db, tenant_id)
        self._contact_repo = PatientContactRepository(db, tenant_id)
        self._visit_history_repo = PatientVisitHistoryRepository(db, tenant_id)
        self._location_repo = LocationRepository(db, tenant_id)

    def list_patients(
        self,
        *,
        search: str | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PatientListItem], int]:
        if search is not None and len(search.strip()) < 2:
            raise ValidationError("search must be at least 2 characters", field="search")

        rows, total = self._repo.search(
            query=search,
            location_id=location_id,
            page=page,
            page_size=page_size,
        )
        return [self._list_item_from(row) for row in rows], total

    def get_patient(self, patient_id: uuid.UUID) -> PatientDetailResponse:
        patient = self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient not found", field="patient_id")
        return self._detail_from(patient)

    def check_duplicates(
        self,
        *,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        exclude_patient_id: uuid.UUID | None = None,
    ) -> DuplicateCheckResponse:
        phone_value = phone.strip() if phone else None
        first_name_value = first_name.strip() if first_name else None
        last_name_value = last_name.strip() if last_name else None

        if not phone_value and not first_name_value:
            raise ValidationError(
                "At least one of phone or first_name is required",
                field="query",
            )

        if phone_value and (not phone_value.isdigit() or len(phone_value) != 10):
            raise ValidationError("phone must be exactly 10 digits", field="phone")

        if first_name_value is not None and len(first_name_value) < 2:
            raise ValidationError("first_name must be at least 2 characters", field="first_name")

        rows = self._repo.find_potential_duplicates(
            phone=phone_value,
            first_name=first_name_value,
            last_name=last_name_value,
            exclude_id=exclude_patient_id,
        )
        matches = [
            DuplicateMatchResponse(
                patient_id=patient.id,
                mrn=patient.mrn,
                first_name=patient.first_name,
                last_name=patient.last_name,
                phone=patient.phone,
                date_of_birth=patient.date_of_birth,
                match_reasons=reasons,  # type: ignore[arg-type]
            )
            for patient, reasons in rows
        ]
        return DuplicateCheckResponse(has_duplicates=len(matches) > 0, matches=matches)

    def create_patient(
        self,
        payload: PatientCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> PatientDetailResponse:
        self._validate_location(payload.location_id)
        assert_trial_patient_capacity(self.db, self.tenant_id)
        if not payload.acknowledge_duplicate:
            self._assert_phone_available(payload.phone)

        mrn = self._repo.generate_mrn()
        consent_given_at = datetime.now(UTC)
        patient = self._repo.create(
            mrn=mrn,
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            phone=payload.phone,
            email=str(payload.email).lower() if payload.email else None,
            blood_group=payload.blood_group,
            address_line1=payload.address_line1,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            photo_url=payload.photo_url,
            id_proof_type=payload.id_proof_type,
            id_proof_number=payload.id_proof_number,
            marital_status=payload.marital_status,
            occupation=payload.occupation,
            consent_given_at=consent_given_at,
            consent_method=payload.consent_method,
            location_id=payload.location_id,
            created_by=actor_id,
        )
        self.db.flush()
        response = self._detail_from(patient)
        self.db.commit()
        return response

    def update_patient(
        self,
        patient_id: uuid.UUID,
        payload: PatientUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> PatientDetailResponse:
        patient = self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient not found", field="patient_id")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        if "location_id" in update_data:
            self._validate_location(update_data["location_id"])

        if "phone" in update_data:
            self._assert_phone_available(update_data["phone"], exclude_id=patient.id)

        if "email" in update_data and update_data["email"] is not None:
            update_data["email"] = str(update_data["email"]).lower()

        for key, value in update_data.items():
            setattr(patient, key, value)

        patient.updated_by = actor_id
        self.db.add(patient)
        response = self._detail_from(patient)
        self.db.commit()
        return response

    def delete_patient(
        self,
        patient_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        patient = self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient not found", field="patient_id")
        self._repo.soft_delete(patient, deleted_by=actor_id)
        self.db.commit()

    def list_allergies(self, patient_id: uuid.UUID) -> list[AllergyResponse]:
        self._require_patient(patient_id)
        rows = self._allergy_repo.list_by_patient(patient_id)
        return [self._allergy_response_from(row) for row in rows]

    def add_allergy(
        self,
        patient_id: uuid.UUID,
        payload: AllergyCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> AllergyResponse:
        self._require_patient(patient_id)
        allergy = self._allergy_repo.create(
            patient_id=patient_id,
            allergen=payload.allergen,
            severity=payload.severity,
            reaction=payload.reaction,
            onset_date=payload.onset_date,
            is_active=payload.is_active,
            created_by=actor_id,
        )
        self.db.flush()
        response = self._allergy_response_from(allergy)
        self.db.commit()
        return response

    def delete_allergy(
        self,
        patient_id: uuid.UUID,
        allergy_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        self._require_patient(patient_id)
        allergy = self._allergy_repo.get_by_id_for_patient(allergy_id, patient_id)
        if allergy is None:
            raise NotFoundError("Allergy not found", field="allergy_id")
        self._allergy_repo.soft_delete(allergy, deleted_by=actor_id)
        self.db.commit()

    def list_contacts(self, patient_id: uuid.UUID) -> list[ContactResponse]:
        self._require_patient(patient_id)
        rows = self._contact_repo.list_by_patient(patient_id)
        return [self._contact_response_from(row) for row in rows]

    def add_contact(
        self,
        patient_id: uuid.UUID,
        payload: ContactCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> ContactResponse:
        self._require_patient(patient_id)
        if payload.is_primary:
            self._contact_repo.clear_primary_for_patient(patient_id)

        contact = self._contact_repo.create(
            patient_id=patient_id,
            name=payload.name,
            relationship=payload.relationship,
            phone=payload.phone,
            email=str(payload.email).lower() if payload.email else None,
            is_emergency=payload.is_emergency,
            is_primary=payload.is_primary,
            created_by=actor_id,
        )
        self.db.flush()
        response = self._contact_response_from(contact)
        self.db.commit()
        return response

    def list_visit_history(
        self,
        patient_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PatientVisitHistoryItem], int]:
        self._require_patient(patient_id)
        return self._visit_history_repo.list_for_patient(
            patient_id,
            page=page,
            page_size=page_size,
        )

    def list_chronic_conditions(self, patient_id: uuid.UUID) -> list[ChronicConditionResponse]:
        patient = self._require_patient(patient_id)
        return self._chronic_conditions_from(patient)

    def add_chronic_condition(
        self,
        patient_id: uuid.UUID,
        payload: ChronicConditionCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> ChronicConditionResponse:
        patient = self._require_patient(patient_id)
        existing = self._chronic_conditions_from(patient)
        normalized_name = payload.condition_name.casefold()
        if any(
            item.condition_name.casefold() == normalized_name and item.status == "active"
            for item in existing
        ):
            raise ConflictError("Active chronic condition already recorded", field="condition_name")

        recorded_at = datetime.now(UTC)
        entry = {
            "id": str(uuid.uuid4()),
            "condition_name": payload.condition_name,
            "icd_code": payload.icd_code,
            "diagnosed_date": payload.diagnosed_date.isoformat() if payload.diagnosed_date else None,
            "status": payload.status,
            "notes": payload.notes,
            "recorded_at": recorded_at.isoformat(),
        }
        conditions = list(patient.chronic_conditions or [])
        conditions.append(entry)
        patient.chronic_conditions = conditions
        patient.updated_by = actor_id
        flag_modified(patient, "chronic_conditions")
        self.db.add(patient)
        self.db.flush()
        response = ChronicConditionResponse(
            id=uuid.UUID(entry["id"]),
            condition_name=entry["condition_name"],
            icd_code=entry["icd_code"],
            diagnosed_date=payload.diagnosed_date,
            status=entry["status"],
            notes=entry["notes"],
            recorded_at=recorded_at,
        )
        self.db.commit()
        return response

    def _require_patient(self, patient_id: uuid.UUID) -> Patient:
        patient = self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient not found", field="patient_id")
        return patient

    def _allergy_response_from(self, allergy) -> AllergyResponse:
        return AllergyResponse(
            id=allergy.id,
            patient_id=allergy.patient_id,
            allergen=allergy.allergen,
            severity=allergy.severity,
            reaction=allergy.reaction,
            onset_date=allergy.onset_date,
            is_active=allergy.is_active,
            created_at=allergy.created_at,
            updated_at=allergy.updated_at,
        )

    def _contact_response_from(self, contact) -> ContactResponse:
        return ContactResponse(
            id=contact.id,
            patient_id=contact.patient_id,
            name=contact.name,
            relationship=contact.relationship,
            phone=contact.phone,
            email=contact.email,
            is_emergency=contact.is_emergency,
            is_primary=contact.is_primary,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )

    def _chronic_conditions_from(self, patient: Patient) -> list[ChronicConditionResponse]:
        items: list[ChronicConditionResponse] = []
        for raw in patient.chronic_conditions or []:
            if not isinstance(raw, dict):
                continue
            condition_id = raw.get("id")
            condition_name = raw.get("condition_name")
            recorded_at = raw.get("recorded_at")
            if not condition_id or not condition_name or not recorded_at:
                continue
            diagnosed_raw = raw.get("diagnosed_date")
            items.append(
                ChronicConditionResponse(
                    id=uuid.UUID(str(condition_id)),
                    condition_name=str(condition_name),
                    icd_code=raw.get("icd_code"),
                    diagnosed_date=(
                        datetime.fromisoformat(str(diagnosed_raw)).date()
                        if diagnosed_raw
                        else None
                    ),
                    status=str(raw.get("status", "active")),
                    notes=raw.get("notes"),
                    recorded_at=datetime.fromisoformat(str(recorded_at)),
                )
            )
        return items

    def _load_allergies(self, patient_id: uuid.UUID) -> list[AllergyResponse]:
        return [
            self._allergy_response_from(row)
            for row in self._allergy_repo.list_by_patient(patient_id)
        ]

    def _load_contacts(self, patient_id: uuid.UUID) -> list[ContactResponse]:
        return [
            self._contact_response_from(row)
            for row in self._contact_repo.list_by_patient(patient_id)
        ]

    def _list_item_from(self, patient: Patient) -> PatientListItem:
        return PatientListItem(
            id=patient.id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            phone=patient.phone,
            email=patient.email,
            blood_group=patient.blood_group,
            last_visit_date=self._visit_history_repo.latest_visit_date(patient.id),
            created_at=patient.created_at,
        )

    def _detail_from(self, patient: Patient) -> PatientDetailResponse:
        return PatientDetailResponse(
            id=patient.id,
            tenant_id=patient.tenant_id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_group=patient.blood_group,
            phone=patient.phone,
            email=patient.email,
            address_line1=patient.address_line1,
            city=patient.city,
            state=patient.state,
            postal_code=patient.postal_code,
            photo_url=patient.photo_url,
            id_proof_type=patient.id_proof_type,
            id_proof_number=patient.id_proof_number,
            marital_status=patient.marital_status,
            occupation=patient.occupation,
            consent_given_at=patient.consent_given_at,
            consent_method=patient.consent_method,
            location_id=patient.location_id,
            chronic_conditions=self._chronic_conditions_from(patient),
            allergies=self._load_allergies(patient.id),
            contacts=self._load_contacts(patient.id),
            last_visit_date=self._visit_history_repo.latest_visit_date(patient.id),
            version=patient.version,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )

    def _validate_location(self, location_id: uuid.UUID | None) -> None:
        if location_id is None:
            return
        if self._location_repo.get_by_id(location_id) is None:
            raise NotFoundError("Location not found", field="location_id")

    def _assert_phone_available(
        self,
        phone: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        existing = self._repo.get_by_phone(phone, exclude_id=exclude_id)
        if existing is not None:
            raise ConflictError(
                "Phone number already registered; check duplicates or set acknowledge_duplicate",
                field="phone",
            )
