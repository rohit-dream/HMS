"""Tenant-scoped doctor schedule management."""

from __future__ import annotations

import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.org.schemas.doctor_schedule import (
    DoctorScheduleCreateRequest,
    DoctorScheduleResponse,
    DoctorScheduleUpdateRequest,
    times_overlap,
)
from app.domains.platform.repositories.location_repository import LocationRepository
from app.models.core.doctor_schedule import DoctorSchedule


class DoctorScheduleService:
    """CRUD for weekly doctor availability slots — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = DoctorScheduleRepository(db, tenant_id)
        self._doctor_repo = DoctorRepository(db, tenant_id)
        self._location_repo = LocationRepository(db, tenant_id)

    def list_schedules(
        self,
        doctor_id: uuid.UUID,
        *,
        day_of_week: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DoctorScheduleResponse], int]:
        self._require_doctor(doctor_id)
        rows, total = self._repo.list_for_doctor(
            doctor_id,
            day_of_week=day_of_week,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
        return [self._response_from(row) for row in rows], total

    def get_schedule(self, doctor_id: uuid.UUID, schedule_id: uuid.UUID) -> DoctorScheduleResponse:
        self._require_doctor(doctor_id)
        schedule = self._repo.get_for_doctor(doctor_id, schedule_id)
        if schedule is None:
            raise NotFoundError("Schedule not found", field="schedule_id")
        return self._response_from(schedule)

    def create_schedule(
        self,
        doctor_id: uuid.UUID,
        payload: DoctorScheduleCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DoctorScheduleResponse:
        self._require_doctor(doctor_id)
        self._validate_location(payload.location_id)
        self._assert_no_overlap(
            doctor_id,
            payload.day_of_week,
            payload.start_time,
            payload.end_time,
        )

        schedule = self._repo.create(
            doctor_id=doctor_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            slot_duration_minutes=payload.slot_duration_minutes,
            max_patients_per_slot=payload.max_patients_per_slot,
            location_id=payload.location_id,
            is_active=payload.is_active,
            created_by=actor_id,
        )
        self.db.flush()
        response = self._response_from(schedule)
        self.db.commit()
        return response

    def update_schedule(
        self,
        doctor_id: uuid.UUID,
        schedule_id: uuid.UUID,
        payload: DoctorScheduleUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DoctorScheduleResponse:
        self._require_doctor(doctor_id)
        schedule = self._repo.get_for_doctor(doctor_id, schedule_id)
        if schedule is None:
            raise NotFoundError("Schedule not found", field="schedule_id")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        if "location_id" in update_data:
            self._validate_location(update_data["location_id"])

        day_of_week = update_data.get("day_of_week", schedule.day_of_week)
        start_time = update_data.get("start_time", schedule.start_time)
        end_time = update_data.get("end_time", schedule.end_time)
        if end_time <= start_time:
            raise ValidationError("end_time must be after start_time", field="end_time")

        will_be_active = update_data.get("is_active", schedule.is_active)
        if will_be_active:
            self._assert_no_overlap(
                doctor_id,
                day_of_week,
                start_time,
                end_time,
                exclude_schedule_id=schedule.id,
            )

        for key, value in update_data.items():
            setattr(schedule, key, value)
        schedule.updated_by = actor_id
        self.db.add(schedule)

        response = self._response_from(schedule)
        self.db.commit()
        return response

    def delete_schedule(
        self,
        doctor_id: uuid.UUID,
        schedule_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DoctorScheduleResponse:
        self._require_doctor(doctor_id)
        schedule = self._repo.get_for_doctor(doctor_id, schedule_id)
        if schedule is None:
            raise NotFoundError("Schedule not found", field="schedule_id")

        self._repo.soft_delete(schedule, deleted_by=actor_id)
        schedule.is_active = False
        self.db.add(schedule)
        response = self._response_from(schedule)
        self.db.commit()
        return response

    def _require_doctor(self, doctor_id: uuid.UUID) -> None:
        if self._doctor_repo.get_by_id(doctor_id) is None:
            raise NotFoundError("Doctor not found", field="doctor_id")

    def _validate_location(self, location_id: uuid.UUID | None) -> None:
        if location_id is None:
            return
        if self._location_repo.get_by_id(location_id) is None:
            raise NotFoundError("Location not found", field="location_id")

    def _assert_no_overlap(
        self,
        doctor_id: uuid.UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        *,
        exclude_schedule_id: uuid.UUID | None = None,
    ) -> None:
        existing = self._repo.list_for_doctor_day(
            doctor_id,
            day_of_week,
            exclude_schedule_id=exclude_schedule_id,
        )
        for row in existing:
            if times_overlap(start_time, end_time, row.start_time, row.end_time):
                raise ConflictError(
                    "Schedule overlaps with an existing slot on this day",
                    field="start_time",
                )

    def _response_from(self, schedule: DoctorSchedule) -> DoctorScheduleResponse:
        return DoctorScheduleResponse.model_validate(schedule)
