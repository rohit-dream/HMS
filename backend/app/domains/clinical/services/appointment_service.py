"""Tenant-scoped appointment CRUD."""

from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.clinical.availability_slots import (
    generate_time_slots,
    schedule_day_of_week,
    slot_is_in_past,
)
from app.domains.clinical.repositories.appointment_repository import (
    AppointmentRepository,
    AppointmentWithDetails,
)
from app.domains.clinical.schemas.appointment import (
    TERMINAL_STATUSES,
    VALID_APPOINTMENT_STATUSES,
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentResponse,
    AppointmentUpdateRequest,
    AvailabilityResponse,
    AvailabilitySlotResponse,
)
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from app.models.clinical.appointment import Appointment
from app.models.core.doctor_schedule import DoctorSchedule


class AppointmentService:
    """CRUD for appointments — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = AppointmentRepository(db, tenant_id)
        self._patient_repo = PatientRepository(db, tenant_id)
        self._doctor_repo = DoctorRepository(db, tenant_id)
        self._schedule_repo = DoctorScheduleRepository(db, tenant_id)
        self._location_repo = LocationRepository(db, tenant_id)

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
    ) -> tuple[list[AppointmentResponse], int]:
        if status is not None and status not in VALID_APPOINTMENT_STATUSES:
            raise ValidationError("Invalid appointment status", field="status")
        if from_date is not None and to_date is not None and to_date < from_date:
            raise ValidationError("to_date must be on or after from_date", field="to_date")

        rows, total = self._repo.list_appointments(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_date=appointment_date,
            from_date=from_date,
            to_date=to_date,
            status=status,
            page=page,
            page_size=page_size,
        )
        return [self._response_from(row) for row in rows], total

    def get_appointment(self, appointment_id: uuid.UUID) -> AppointmentResponse:
        row = self._repo.get_with_details(appointment_id)
        if row is None:
            raise NotFoundError("Appointment not found", field="appointment_id")
        return self._response_from(row)

    def get_availability(
        self,
        *,
        doctor_id: uuid.UUID,
        appointment_date: date,
        location_id: uuid.UUID | None = None,
    ) -> AvailabilityResponse:
        self._validate_doctor_for_availability(doctor_id)
        self._validate_location(location_id)
        self._assert_not_past_date(appointment_date)

        schedules = self._matching_schedules(
            doctor_id,
            appointment_date,
            location_id=location_id,
        )
        booked_times = self._repo.list_booked_start_times(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
        )

        slot_map: dict[time, AvailabilitySlotResponse] = {}
        for schedule in schedules:
            for start, end in generate_time_slots(
                schedule.start_time,
                schedule.end_time,
                schedule.slot_duration_minutes,
            ):
                if start in slot_map:
                    continue
                available = start not in booked_times and not slot_is_in_past(
                    appointment_date,
                    start,
                )
                slot_map[start] = AvailabilitySlotResponse(
                    start_time=start,
                    end_time=end,
                    available=available,
                )

        slots = sorted(slot_map.values(), key=lambda slot: slot.start_time)
        return AvailabilityResponse(
            doctor_id=doctor_id,
            date=appointment_date,
            slots=slots,
        )

    def create_appointment(
        self,
        payload: AppointmentCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> AppointmentResponse:
        self._validate_patient(payload.patient_id)
        self._validate_doctor(payload.doctor_id)
        self._validate_location(payload.location_id)
        self._assert_not_past_date(payload.appointment_date)
        self._assert_slot_in_schedule(
            doctor_id=payload.doctor_id,
            appointment_date=payload.appointment_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location_id=payload.location_id,
        )

        if self._repo.has_active_slot_conflict(
            doctor_id=payload.doctor_id,
            appointment_date=payload.appointment_date,
            start_time=payload.start_time,
        ):
            raise ConflictError("This doctor slot is already booked", field="start_time")

        appointment = self._repo.create(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            location_id=payload.location_id,
            appointment_date=payload.appointment_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            appointment_type=payload.appointment_type,
            status="scheduled",
            is_walk_in=payload.is_walk_in,
            notes=payload.notes,
            created_by=actor_id,
        )

        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("This doctor slot is already booked", field="start_time") from exc

        row = self._repo.get_with_details(appointment.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def update_appointment(
        self,
        appointment_id: uuid.UUID,
        payload: AppointmentUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> AppointmentResponse:
        appointment = self._repo.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment not found", field="appointment_id")

        if appointment.status in TERMINAL_STATUSES:
            raise ValidationError(
                f"Cannot update a {appointment.status} appointment",
                field="status",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        if "location_id" in update_data:
            self._validate_location(update_data["location_id"])

        appointment_date = update_data.get("appointment_date", appointment.appointment_date)
        start_time = update_data.get("start_time", appointment.start_time)
        end_time = update_data.get("end_time", appointment.end_time)

        if end_time <= start_time:
            raise ValidationError("end_time must be after start_time", field="end_time")

        if "appointment_date" in update_data:
            self._assert_not_past_date(appointment_date)

        slot_changed = (
            appointment_date != appointment.appointment_date
            or start_time != appointment.start_time
            or end_time != appointment.end_time
        )
        if slot_changed:
            self._assert_slot_in_schedule(
                doctor_id=appointment.doctor_id,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                location_id=update_data.get("location_id", appointment.location_id),
            )

        if slot_changed and self._repo.has_active_slot_conflict(
            doctor_id=appointment.doctor_id,
            appointment_date=appointment_date,
            start_time=start_time,
            exclude_appointment_id=appointment.id,
        ):
            raise ConflictError("This doctor slot is already booked", field="start_time")

        for key, value in update_data.items():
            setattr(appointment, key, value)
        appointment.updated_by = actor_id
        self.db.add(appointment)

        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("This doctor slot is already booked", field="start_time") from exc

        row = self._repo.get_with_details(appointment.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def delete_appointment(
        self,
        appointment_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        appointment = self._repo.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment not found", field="appointment_id")

        self._repo.soft_delete(appointment, deleted_by=actor_id)
        self.db.commit()

    def confirm_appointment(
        self,
        appointment_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> AppointmentResponse:
        appointment = self._repo.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment not found", field="appointment_id")

        if appointment.status != "scheduled":
            raise ValidationError(
                f"Cannot confirm an appointment with status '{appointment.status}'",
                field="status",
            )

        appointment.status = "confirmed"
        appointment.updated_by = actor_id
        self.db.add(appointment)

        row = self._repo.get_with_details(appointment.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        payload: AppointmentCancelRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> AppointmentResponse:
        appointment = self._repo.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment not found", field="appointment_id")

        if appointment.status in TERMINAL_STATUSES:
            raise ValidationError(
                f"Cannot cancel an appointment with status '{appointment.status}'",
                field="status",
            )

        appointment.status = "cancelled"
        appointment.cancelled_reason = payload.cancelled_reason
        appointment.updated_by = actor_id
        self.db.add(appointment)

        row = self._repo.get_with_details(appointment.id)
        assert row is not None
        response = self._response_from(row)
        self.db.commit()
        return response

    def _validate_patient(self, patient_id: uuid.UUID) -> None:
        if self._patient_repo.get_by_id(patient_id) is None:
            raise NotFoundError("Patient not found", field="patient_id")

    def _validate_doctor(self, doctor_id: uuid.UUID) -> None:
        doctor = self._doctor_repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor not found", field="doctor_id")
        if not doctor.is_available:
            raise ValidationError("Doctor is not available for booking", field="doctor_id")

    def _validate_doctor_for_availability(self, doctor_id: uuid.UUID) -> None:
        if self._doctor_repo.get_by_id(doctor_id) is None:
            raise NotFoundError("Doctor not found", field="doctor_id")

    def _matching_schedules(
        self,
        doctor_id: uuid.UUID,
        appointment_date: date,
        *,
        location_id: uuid.UUID | None,
    ) -> list[DoctorSchedule]:
        day = schedule_day_of_week(appointment_date)
        schedules = self._schedule_repo.list_for_doctor_day(doctor_id, day)
        if location_id is None:
            return schedules
        return [
            schedule
            for schedule in schedules
            if schedule.location_id is None or schedule.location_id == location_id
        ]

    def _assert_slot_in_schedule(
        self,
        *,
        doctor_id: uuid.UUID,
        appointment_date: date,
        start_time: time,
        end_time: time,
        location_id: uuid.UUID | None,
    ) -> None:
        schedules = self._matching_schedules(
            doctor_id,
            appointment_date,
            location_id=location_id,
        )
        if not schedules:
            raise ValidationError(
                "Doctor has no schedule for this date",
                field="appointment_date",
            )

        for schedule in schedules:
            for slot_start, slot_end in generate_time_slots(
                schedule.start_time,
                schedule.end_time,
                schedule.slot_duration_minutes,
            ):
                if slot_start == start_time and slot_end == end_time:
                    if slot_is_in_past(appointment_date, start_time):
                        raise ValidationError(
                            "Cannot book a slot in the past",
                            field="start_time",
                        )
                    return

        raise ValidationError(
            "Requested slot is outside the doctor schedule",
            field="start_time",
        )

    def _validate_location(self, location_id: uuid.UUID | None) -> None:
        if location_id is None:
            return
        if self._location_repo.get_by_id(location_id) is None:
            raise NotFoundError("Location not found", field="location_id")

    def _assert_not_past_date(self, appointment_date: date) -> None:
        if appointment_date < date.today():
            raise ValidationError("appointment_date cannot be in the past", field="appointment_date")

    def _response_from(self, row: AppointmentWithDetails) -> AppointmentResponse:
        patient_name = f"{row.patient.first_name} {row.patient.last_name or ''}".strip()
        doctor_name = f"Dr. {row.staff.first_name} {row.staff.last_name}".strip()
        appt: Appointment = row.appointment
        return AppointmentResponse(
            id=appt.id,
            tenant_id=appt.tenant_id,
            patient_id=appt.patient_id,
            patient_name=patient_name,
            doctor_id=appt.doctor_id,
            doctor_name=doctor_name,
            location_id=appt.location_id,
            appointment_date=appt.appointment_date,
            start_time=appt.start_time,
            end_time=appt.end_time,
            appointment_type=appt.appointment_type,
            status=appt.status,
            is_walk_in=appt.is_walk_in,
            notes=appt.notes,
            cancelled_reason=appt.cancelled_reason,
            created_at=appt.created_at,
            updated_at=appt.updated_at,
        )
