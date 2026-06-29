"""clinical.opd_visits data access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select, text

from app.models.clinical.opd import (
    OpdClinicalNote,
    OpdPrescription,
    OpdQueue,
    OpdVitals,
    OpdVisit,
)
from app.models.core.doctor import Doctor
from app.models.core.patient import Patient
from app.models.core.staff import Staff
from app.models.platform.tenant_location import TenantLocation
from app.repositories.base import TenantScopedRepository


@dataclass(frozen=True)
class OpdVisitWithDetails:
    visit: OpdVisit
    patient: Patient
    doctor: Doctor
    staff: Staff
    location: TenantLocation | None
    queue_id: uuid.UUID | None = None


class OpdVisitRepository(TenantScopedRepository):
    def generate_visit_number(self) -> str:
        return self.db.execute(
            text("SELECT clinical.generate_visit_number(:tenant_id)"),
            {"tenant_id": self.tenant_id},
        ).scalar_one()

    def get_by_id(self, visit_id: uuid.UUID) -> OpdVisit | None:
        return super().get_by_id(OpdVisit, visit_id)

    def get_with_details(self, visit_id: uuid.UUID) -> OpdVisitWithDetails | None:
        stmt = (
            select(OpdVisit, Patient, Doctor, Staff, TenantLocation)
            .join(
                Patient,
                (OpdVisit.tenant_id == Patient.tenant_id) & (OpdVisit.patient_id == Patient.id),
            )
            .join(
                Doctor,
                (OpdVisit.tenant_id == Doctor.tenant_id) & (OpdVisit.doctor_id == Doctor.id),
            )
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .outerjoin(
                TenantLocation,
                (OpdVisit.tenant_id == TenantLocation.tenant_id)
                & (OpdVisit.location_id == TenantLocation.id),
            )
            .where(
                OpdVisit.tenant_id == self.tenant_id,
                OpdVisit.id == visit_id,
                OpdVisit.deleted_at.is_(None),
                Patient.deleted_at.is_(None),
                Doctor.deleted_at.is_(None),
                Staff.deleted_at.is_(None),
            )
        )
        row = self.db.execute(stmt).first()
        if row is None:
            return None

        queue_id = self.get_active_queue_id(visit_id)
        return OpdVisitWithDetails(
            visit=row[0],
            patient=row[1],
            doctor=row[2],
            staff=row[3],
            location=row[4],
            queue_id=queue_id,
        )

    def get_active_queue_id(self, visit_id: uuid.UUID) -> uuid.UUID | None:
        stmt = self._base_query(OpdQueue).where(
            OpdQueue.opd_visit_id == visit_id,
            OpdQueue.status.notin_(("completed", "skipped")),
        )
        entry = self.db.scalars(stmt).first()
        return entry.id if entry else None

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
    ) -> tuple[list[OpdVisitWithDetails], int]:
        base_filters = [
            OpdVisit.tenant_id == self.tenant_id,
            OpdVisit.deleted_at.is_(None),
            Patient.deleted_at.is_(None),
            Doctor.deleted_at.is_(None),
            Staff.deleted_at.is_(None),
        ]

        if doctor_id is not None:
            base_filters.append(OpdVisit.doctor_id == doctor_id)
        if patient_id is not None:
            base_filters.append(OpdVisit.patient_id == patient_id)
        if visit_date is not None:
            base_filters.append(OpdVisit.visit_date == visit_date)
        if from_date is not None:
            base_filters.append(OpdVisit.visit_date >= from_date)
        if to_date is not None:
            base_filters.append(OpdVisit.visit_date <= to_date)
        if status is not None:
            base_filters.append(OpdVisit.status == status)
        if visit_type is not None:
            base_filters.append(OpdVisit.visit_type == visit_type)
        if location_id is not None:
            base_filters.append(OpdVisit.location_id == location_id)

        count_stmt = (
            select(func.count())
            .select_from(OpdVisit)
            .join(
                Patient,
                (OpdVisit.tenant_id == Patient.tenant_id) & (OpdVisit.patient_id == Patient.id),
            )
            .join(
                Doctor,
                (OpdVisit.tenant_id == Doctor.tenant_id) & (OpdVisit.doctor_id == Doctor.id),
            )
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(*base_filters)
        )
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(OpdVisit, Patient, Doctor, Staff, TenantLocation)
            .join(
                Patient,
                (OpdVisit.tenant_id == Patient.tenant_id) & (OpdVisit.patient_id == Patient.id),
            )
            .join(
                Doctor,
                (OpdVisit.tenant_id == Doctor.tenant_id) & (OpdVisit.doctor_id == Doctor.id),
            )
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .outerjoin(
                TenantLocation,
                (OpdVisit.tenant_id == TenantLocation.tenant_id)
                & (OpdVisit.location_id == TenantLocation.id),
            )
            .where(*base_filters)
            .order_by(OpdVisit.visit_date.desc(), OpdVisit.token_number.nulls_last())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows: list[OpdVisitWithDetails] = []
        for visit, patient, doctor, staff, location in self.db.execute(stmt).all():
            rows.append(
                OpdVisitWithDetails(
                    visit=visit,
                    patient=patient,
                    doctor=doctor,
                    staff=staff,
                    location=location,
                    queue_id=self.get_active_queue_id(visit.id),
                )
            )
        return rows, int(total)

    def create(self, **kwargs: object) -> OpdVisit:
        visit = OpdVisit(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(visit)
        return visit

    def has_active_visit_for_patient_doctor_date(
        self,
        *,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        visit_date: date,
        exclude_visit_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = self._base_query(OpdVisit).where(
            OpdVisit.patient_id == patient_id,
            OpdVisit.doctor_id == doctor_id,
            OpdVisit.visit_date == visit_date,
            OpdVisit.status.notin_(("cancelled", "completed")),
        )
        if exclude_visit_id is not None:
            stmt = stmt.where(OpdVisit.id != exclude_visit_id)
        return self.db.scalars(stmt).first() is not None

    def has_visit_for_appointment(
        self,
        appointment_id: uuid.UUID,
        *,
        exclude_visit_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = self._base_query(OpdVisit).where(
            OpdVisit.appointment_id == appointment_id,
            OpdVisit.status != "cancelled",
        )
        if exclude_visit_id is not None:
            stmt = stmt.where(OpdVisit.id != exclude_visit_id)
        return self.db.scalars(stmt).first() is not None

    def count_vitals(self, visit_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(OpdVitals)
            .where(
                OpdVitals.tenant_id == self.tenant_id,
                OpdVitals.opd_visit_id == visit_id,
                OpdVitals.deleted_at.is_(None),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def count_notes(self, visit_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(OpdClinicalNote)
            .where(
                OpdClinicalNote.tenant_id == self.tenant_id,
                OpdClinicalNote.opd_visit_id == visit_id,
                OpdClinicalNote.deleted_at.is_(None),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def count_prescriptions(self, visit_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(OpdPrescription)
            .where(
                OpdPrescription.tenant_id == self.tenant_id,
                OpdPrescription.opd_visit_id == visit_id,
                OpdPrescription.deleted_at.is_(None),
            )
        )
        return int(self.db.scalar(stmt) or 0)

    def finalize_notes(self, visit_id: uuid.UUID) -> None:
        stmt = select(OpdClinicalNote).where(
            OpdClinicalNote.tenant_id == self.tenant_id,
            OpdClinicalNote.opd_visit_id == visit_id,
            OpdClinicalNote.deleted_at.is_(None),
            OpdClinicalNote.is_final.is_(False),
        )
        for note in self.db.scalars(stmt).all():
            note.is_final = True
            self.db.add(note)
