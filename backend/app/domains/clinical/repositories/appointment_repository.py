"""clinical.appointments data access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, time

from sqlalchemy import func, select

from app.models.clinical.appointment import Appointment
from app.models.core.doctor import Doctor
from app.models.core.patient import Patient
from app.models.core.staff import Staff
from app.repositories.base import TenantScopedRepository


@dataclass(frozen=True)
class AppointmentWithDetails:
    appointment: Appointment
    patient: Patient
    doctor: Doctor
    staff: Staff


class AppointmentRepository(TenantScopedRepository):
    def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        return super().get_by_id(Appointment, appointment_id)

    def get_with_details(self, appointment_id: uuid.UUID) -> AppointmentWithDetails | None:
        stmt = (
            select(Appointment, Patient, Doctor, Staff)
            .join(
                Patient,
                (Appointment.tenant_id == Patient.tenant_id)
                & (Appointment.patient_id == Patient.id),
            )
            .join(
                Doctor,
                (Appointment.tenant_id == Doctor.tenant_id)
                & (Appointment.doctor_id == Doctor.id),
            )
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(
                Appointment.tenant_id == self.tenant_id,
                Appointment.id == appointment_id,
                Appointment.deleted_at.is_(None),
                Patient.deleted_at.is_(None),
                Doctor.deleted_at.is_(None),
                Staff.deleted_at.is_(None),
            )
        )
        row = self.db.execute(stmt).first()
        if row is None:
            return None
        return AppointmentWithDetails(
            appointment=row[0],
            patient=row[1],
            doctor=row[2],
            staff=row[3],
        )

    def list_appointments(
        self,
        *,
        doctor_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
        appointment_date: date | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AppointmentWithDetails], int]:
        base_filters = [
            Appointment.tenant_id == self.tenant_id,
            Appointment.deleted_at.is_(None),
            Patient.deleted_at.is_(None),
            Doctor.deleted_at.is_(None),
            Staff.deleted_at.is_(None),
        ]

        if doctor_id is not None:
            base_filters.append(Appointment.doctor_id == doctor_id)
        if patient_id is not None:
            base_filters.append(Appointment.patient_id == patient_id)
        if appointment_date is not None:
            base_filters.append(Appointment.appointment_date == appointment_date)
        if from_date is not None:
            base_filters.append(Appointment.appointment_date >= from_date)
        if to_date is not None:
            base_filters.append(Appointment.appointment_date <= to_date)
        if status is not None:
            base_filters.append(Appointment.status == status)

        count_stmt = (
            select(func.count())
            .select_from(Appointment)
            .join(
                Patient,
                (Appointment.tenant_id == Patient.tenant_id)
                & (Appointment.patient_id == Patient.id),
            )
            .join(
                Doctor,
                (Appointment.tenant_id == Doctor.tenant_id)
                & (Appointment.doctor_id == Doctor.id),
            )
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(*base_filters)
        )
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Appointment, Patient, Doctor, Staff)
            .join(
                Patient,
                (Appointment.tenant_id == Patient.tenant_id)
                & (Appointment.patient_id == Patient.id),
            )
            .join(
                Doctor,
                (Appointment.tenant_id == Doctor.tenant_id)
                & (Appointment.doctor_id == Doctor.id),
            )
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(*base_filters)
            .order_by(
                Appointment.appointment_date.desc(),
                Appointment.start_time,
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = [
            AppointmentWithDetails(appointment=appt, patient=pat, doctor=doc, staff=st)
            for appt, pat, doc, st in self.db.execute(stmt).all()
        ]
        return rows, int(total)

    def create(self, **kwargs: object) -> Appointment:
        appointment = Appointment(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(appointment)
        return appointment

    def has_active_slot_conflict(
        self,
        *,
        doctor_id: uuid.UUID,
        appointment_date: date,
        start_time: time,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = self._base_query(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.start_time == start_time,
            Appointment.status.notin_(("cancelled", "no_show")),
        )
        if exclude_appointment_id is not None:
            stmt = stmt.where(Appointment.id != exclude_appointment_id)
        return self.db.scalars(stmt).first() is not None

    def list_booked_start_times(
        self,
        *,
        doctor_id: uuid.UUID,
        appointment_date: date,
    ) -> set[time]:
        stmt = self._base_query(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.notin_(("cancelled", "no_show")),
        )
        return {row.start_time for row in self.db.scalars(stmt).all()}
