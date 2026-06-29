"""Tenant-scoped OPD visit lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.clinical.repositories.appointment_repository import AppointmentRepository
from app.domains.clinical.repositories.opd_queue_repository import (
    OpdQueueEntryWithDetails,
    OpdQueueRepository,
)
from app.domains.clinical.repositories.opd_visit_repository import (
    OpdVisitRepository,
    OpdVisitWithDetails,
)
from app.domains.clinical.repositories.opd_vitals_repository import OpdVitalsRepository
from app.domains.clinical.schemas.opd.queue import OpdQueueEntryResponse
from app.domains.clinical.schemas.opd.vitals import OpdVitalsResponse
from app.domains.clinical.schemas.opd.visit import (
    OpdVisitCancelRequest,
    OpdVisitCompleteRequest,
    OpdVisitCompleteResponse,
    OpdVisitCreateRequest,
    OpdVisitDetailResponse,
    OpdVisitResponse,
    OpdVisitStartRequest,
    OpdVisitUpdateRequest,
)
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from app.models.clinical.appointment import Appointment
from app.models.clinical.opd import OpdQueue, OpdVitals, OpdVisit

VALID_VISIT_STATUSES = frozenset({"waiting", "in_consultation", "completed", "cancelled"})
VALID_VISIT_TYPES = frozenset({"walk_in", "appointment"})
TERMINAL_VISIT_STATUSES = frozenset({"completed", "cancelled"})


class OpdVisitService:
    """OPD visits — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = OpdVisitRepository(db, tenant_id)
        self._queue_repo = OpdQueueRepository(db, tenant_id)
        self._vitals_repo = OpdVitalsRepository(db, tenant_id)
        self._patient_repo = PatientRepository(db, tenant_id)
        self._doctor_repo = DoctorRepository(db, tenant_id)
        self._location_repo = LocationRepository(db, tenant_id)
        self._appointment_repo = AppointmentRepository(db, tenant_id)

    def list_visits(
        self,
        *,
        doctor_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
        visit_date: date | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        status: str | None = None,
        visit_type: str | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[OpdVisitResponse], int]:
        if status is not None and status not in VALID_VISIT_STATUSES:
            raise ValidationError("Invalid visit status", field="status")
        if visit_type is not None and visit_type not in VALID_VISIT_TYPES:
            raise ValidationError("Invalid visit type", field="visit_type")
        if from_date is not None and to_date is not None and to_date < from_date:
            raise ValidationError("to_date must be on or after from_date", field="to_date")

        rows, total = self._repo.list_visits(
            doctor_id=doctor_id,
            patient_id=patient_id,
            visit_date=visit_date,
            from_date=from_date,
            to_date=to_date,
            status=status,
            visit_type=visit_type,
            location_id=location_id,
            page=page,
            page_size=page_size,
        )
        return [self._response_from(row) for row in rows], total

    def get_visit(self, visit_id: uuid.UUID) -> OpdVisitDetailResponse:
        row = self._repo.get_with_details(visit_id)
        if row is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        response = self._detail_from(row)
        self.db.commit()
        return response

    def create_visit(
        self,
        payload: OpdVisitCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdVisitResponse:
        visit_date = payload.visit_date or date.today()
        self._assert_visit_date_allowed(visit_date)
        self._validate_patient(payload.patient_id)
        self._validate_doctor(payload.doctor_id)
        self._validate_location(payload.location_id)

        appointment: Appointment | None = None
        if payload.visit_type == "appointment":
            if payload.appointment_id is None:
                raise ValidationError(
                    "appointment_id is required for appointment visits",
                    field="appointment_id",
                )
            appointment = self._validate_appointment_for_visit(
                appointment_id=payload.appointment_id,
                patient_id=payload.patient_id,
                doctor_id=payload.doctor_id,
                visit_date=visit_date,
            )
        elif payload.appointment_id is not None:
            raise ValidationError(
                "appointment_id is only allowed when visit_type is appointment",
                field="appointment_id",
            )

        if appointment is not None and self._repo.has_visit_for_appointment(appointment.id):
            raise ConflictError(
                "This appointment already has an OPD visit",
                field="appointment_id",
            )

        if self._repo.has_active_visit_for_patient_doctor_date(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            visit_date=visit_date,
        ):
            raise ConflictError(
                "An active OPD visit already exists for this patient, doctor, and date",
                field="patient_id",
            )

        visit_number = self._repo.generate_visit_number()
        token_number: int | None = None
        queue_entry: OpdQueue | None = None

        visit = self._repo.create(
            visit_number=visit_number,
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            appointment_id=payload.appointment_id,
            location_id=payload.location_id,
            visit_date=visit_date,
            visit_type=payload.visit_type,
            status="waiting",
            chief_complaint=payload.chief_complaint,
            created_by=actor_id,
        )
        self.db.flush()

        if payload.add_to_queue:
            token_number = self._queue_repo.next_token_number(
                doctor_id=payload.doctor_id,
                queue_date=visit_date,
            )
            visit.token_number = token_number
            queue_entry = self._queue_repo.create(
                opd_visit_id=visit.id,
                doctor_id=payload.doctor_id,
                token_number=token_number,
                queue_date=visit_date,
                status="waiting",
                priority=payload.queue_priority,
                created_by=actor_id,
            )
            self.db.add(visit)

        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            if "uq_opd_visits_tenant_appointment_active" in str(exc):
                raise ConflictError(
                    "This appointment already has an OPD visit",
                    field="appointment_id",
                ) from exc
            raise ConflictError(
                "An active OPD visit already exists for this patient, doctor, and date",
                field="patient_id",
            ) from exc

        row = self._repo.get_with_details(visit.id)
        assert row is not None
        if queue_entry is not None:
            row = OpdVisitWithDetails(
                visit=row.visit,
                patient=row.patient,
                doctor=row.doctor,
                staff=row.staff,
                location=row.location,
                queue_id=queue_entry.id,
            )
        response = self._response_from(row)
        self.db.commit()
        return response

    def update_visit(
        self,
        visit_id: uuid.UUID,
        payload: OpdVisitUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdVisitResponse:
        visit = self._repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status != "waiting":
            raise ConflictError(
                "Visit metadata can only be updated while waiting",
                field="status",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        if "doctor_id" in update_data:
            self._validate_doctor(update_data["doctor_id"])
        if "location_id" in update_data:
            self._validate_location(update_data["location_id"])

        for key, value in update_data.items():
            setattr(visit, key, value)
        visit.updated_by = actor_id
        self.db.add(visit)
        self.db.flush()

        row = self._repo.get_with_details(visit.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def cancel_visit(
        self,
        visit_id: uuid.UUID,
        payload: OpdVisitCancelRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdVisitResponse:
        visit = self._repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status in TERMINAL_VISIT_STATUSES:
            raise ConflictError(
                f"Cannot cancel visit in status {visit.status}",
                field="status",
            )

        visit.status = "cancelled"
        visit.updated_by = actor_id
        self.db.add(visit)

        queue_entry = self._queue_repo.get_active_for_visit(visit_id)
        if queue_entry is not None:
            queue_entry.status = "skipped"
            queue_entry.updated_by = actor_id
            self.db.add(queue_entry)

        self.db.flush()
        row = self._repo.get_with_details(visit.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def start_visit(
        self,
        visit_id: uuid.UUID,
        payload: OpdVisitStartRequest | None = None,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdVisitResponse:
        visit = self._repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status != "waiting":
            raise ConflictError(
                "Consultation can only start from waiting status",
                field="status",
            )

        if payload is not None and payload.doctor_id is not None:
            if payload.doctor_id != visit.doctor_id:
                self._validate_doctor(payload.doctor_id)
                visit.doctor_id = payload.doctor_id

        now = datetime.now(UTC)
        visit.status = "in_consultation"
        visit.started_at = now
        visit.updated_by = actor_id
        self.db.add(visit)

        queue_entry = self._queue_repo.get_active_for_visit(visit_id)
        if queue_entry is not None:
            queue_entry.status = "in_consultation"
            queue_entry.updated_by = actor_id
            self.db.add(queue_entry)

        self.db.flush()
        row = self._repo.get_with_details(visit.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def complete_visit(
        self,
        visit_id: uuid.UUID,
        payload: OpdVisitCompleteRequest | None = None,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdVisitCompleteResponse:
        visit = self._repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status != "in_consultation":
            raise ConflictError(
                "Visit must be in consultation to complete",
                field="status",
            )

        options = payload or OpdVisitCompleteRequest()
        now = datetime.now(UTC)
        visit.status = "completed"
        visit.completed_at = now
        visit.updated_by = actor_id
        self.db.add(visit)

        queue_entry = self._queue_repo.get_active_for_visit(visit_id)
        if queue_entry is not None:
            queue_entry.status = "completed"
            queue_entry.updated_by = actor_id
            self.db.add(queue_entry)

        if options.finalize_notes:
            self._repo.finalize_notes(visit_id)

        if visit.appointment_id is not None:
            appointment = self._appointment_repo.get_by_id(visit.appointment_id)
            if appointment is not None and appointment.status not in ("cancelled", "no_show"):
                appointment.status = "completed"
                appointment.updated_by = actor_id
                self.db.add(appointment)

        self.db.flush()
        self.db.commit()
        return OpdVisitCompleteResponse(
            id=visit.id,
            status="completed",
            completed_at=now,
            billing_invoice_id=None,
        )

    def _validate_patient(self, patient_id: uuid.UUID) -> None:
        if self._patient_repo.get_by_id(patient_id) is None:
            raise NotFoundError("Patient not found", field="patient_id")

    def _validate_doctor(self, doctor_id: uuid.UUID) -> None:
        row = self._doctor_repo.get_with_staff(doctor_id)
        if row is None:
            raise NotFoundError("Doctor not found", field="doctor_id")
        if row.staff.status != "active":
            raise ValidationError("Doctor is not active", field="doctor_id")
        if not row.doctor.is_available:
            raise ValidationError("Doctor is not available for OPD", field="doctor_id")

    def _validate_location(self, location_id: uuid.UUID | None) -> None:
        if location_id is None:
            return
        if self._location_repo.get_by_id(location_id) is None:
            raise NotFoundError("Location not found", field="location_id")

    def _validate_appointment_for_visit(
        self,
        *,
        appointment_id: uuid.UUID,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        visit_date: date,
    ) -> Appointment:
        appointment = self._appointment_repo.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment not found", field="appointment_id")
        if appointment.status != "confirmed":
            raise ValidationError(
                "Appointment must be confirmed to create an OPD visit",
                field="appointment_id",
            )
        if appointment.patient_id != patient_id:
            raise ValidationError(
                "Appointment patient does not match visit patient",
                field="patient_id",
            )
        if appointment.doctor_id != doctor_id:
            raise ValidationError(
                "Appointment doctor does not match visit doctor",
                field="doctor_id",
            )
        if appointment.appointment_date != visit_date:
            raise ValidationError(
                "Appointment date does not match visit date",
                field="visit_date",
            )
        return appointment

    def _assert_visit_date_allowed(self, visit_date: date) -> None:
        earliest = date.today() - timedelta(days=30)
        if visit_date < earliest:
            raise ValidationError(
                "visit_date cannot be more than 30 days in the past",
                field="visit_date",
            )

    def _response_from(self, row: OpdVisitWithDetails) -> OpdVisitResponse:
        visit = row.visit
        return OpdVisitResponse(
            id=visit.id,
            tenant_id=visit.tenant_id,
            visit_number=visit.visit_number,
            patient_id=visit.patient_id,
            patient_name=f"{row.patient.first_name} {row.patient.last_name}".strip(),
            patient_mrn=row.patient.mrn,
            doctor_id=visit.doctor_id,
            doctor_name=f"Dr. {row.staff.first_name} {row.staff.last_name}".strip(),
            appointment_id=visit.appointment_id,
            location_id=visit.location_id,
            location_name=row.location.name if row.location else None,
            visit_date=visit.visit_date,
            visit_type=visit.visit_type,  # type: ignore[arg-type]
            status=visit.status,  # type: ignore[arg-type]
            token_number=visit.token_number,
            chief_complaint=visit.chief_complaint,
            started_at=visit.started_at,
            completed_at=visit.completed_at,
            queue_id=row.queue_id,
            created_at=visit.created_at,
            updated_at=visit.updated_at or visit.created_at,
        )

    def _detail_from(self, row: OpdVisitWithDetails) -> OpdVisitDetailResponse:
        base = self._response_from(row)
        visit_id = row.visit.id
        latest_vitals_row = self._vitals_repo.get_latest_for_visit(visit_id)
        queue_row = self._queue_repo.get_active_with_details_for_visit(visit_id)
        return OpdVisitDetailResponse(
            **base.model_dump(),
            vitals_count=self._repo.count_vitals(visit_id),
            notes_count=self._repo.count_notes(visit_id),
            prescriptions_count=self._repo.count_prescriptions(visit_id),
            latest_vitals=self._vitals_response_from(latest_vitals_row)
            if latest_vitals_row is not None
            else None,
            queue=self._queue_entry_response_from(queue_row) if queue_row is not None else None,
        )

    def _vitals_response_from(self, vitals: OpdVitals) -> OpdVitalsResponse:
        return OpdVitalsResponse(
            id=vitals.id,
            opd_visit_id=vitals.opd_visit_id,
            recorded_at=vitals.recorded_at,
            recorded_by_user_id=vitals.created_by,
            blood_pressure_systolic=vitals.blood_pressure_systolic,
            blood_pressure_diastolic=vitals.blood_pressure_diastolic,
            pulse_rate=vitals.pulse_rate,
            temperature=vitals.temperature,
            temperature_unit="celsius",
            respiratory_rate=vitals.respiratory_rate,
            spo2=vitals.spo2,
            weight_kg=vitals.weight_kg,
            height_cm=vitals.height_cm,
            bmi=vitals.bmi,
            notes=vitals.notes,
        )

    def _queue_entry_response_from(
        self,
        row: OpdQueueEntryWithDetails,
    ) -> OpdQueueEntryResponse:
        queue = row.queue
        visit = row.visit
        return OpdQueueEntryResponse(
            id=queue.id,
            opd_visit_id=queue.opd_visit_id,
            doctor_id=queue.doctor_id,
            patient_id=visit.patient_id,
            patient_name=f"{row.patient.first_name} {row.patient.last_name}".strip(),
            token_number=queue.token_number,
            queue_date=queue.queue_date,
            status=queue.status,  # type: ignore[arg-type]
            priority=queue.priority,  # type: ignore[arg-type]
            chief_complaint=visit.chief_complaint,
            called_at=queue.called_at,
            visit_status=visit.status,  # type: ignore[arg-type]
        )
