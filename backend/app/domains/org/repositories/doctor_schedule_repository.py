"""core.doctor_schedules data access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.core.doctor_schedule import DoctorSchedule
from app.repositories.base import TenantScopedRepository


class DoctorScheduleRepository(TenantScopedRepository):
    def get_by_id(self, schedule_id: uuid.UUID) -> DoctorSchedule | None:
        return super().get_by_id(DoctorSchedule, schedule_id)

    def get_for_doctor(
        self,
        doctor_id: uuid.UUID,
        schedule_id: uuid.UUID,
    ) -> DoctorSchedule | None:
        stmt = self._base_query(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.id == schedule_id,
        )
        return self.db.scalars(stmt).first()

    def list_for_doctor(
        self,
        doctor_id: uuid.UUID,
        *,
        day_of_week: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DoctorSchedule], int]:
        filters = [DoctorSchedule.doctor_id == doctor_id]
        if day_of_week is not None:
            filters.append(DoctorSchedule.day_of_week == day_of_week)
        if is_active is not None:
            filters.append(DoctorSchedule.is_active.is_(is_active))

        count_stmt = (
            select(func.count())
            .select_from(DoctorSchedule)
            .where(
                DoctorSchedule.tenant_id == self.tenant_id,
                DoctorSchedule.deleted_at.is_(None),
                *filters,
            )
        )
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            self._base_query(DoctorSchedule)
            .where(*filters)
            .order_by(DoctorSchedule.day_of_week, DoctorSchedule.start_time)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(self.db.scalars(stmt).all())
        return rows, int(total)

    def list_for_doctor_day(
        self,
        doctor_id: uuid.UUID,
        day_of_week: int,
        *,
        exclude_schedule_id: uuid.UUID | None = None,
    ) -> list[DoctorSchedule]:
        filters = [
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.day_of_week == day_of_week,
            DoctorSchedule.is_active.is_(True),
        ]
        if exclude_schedule_id is not None:
            filters.append(DoctorSchedule.id != exclude_schedule_id)

        stmt = (
            self._base_query(DoctorSchedule)
            .where(*filters)
            .order_by(DoctorSchedule.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def create(self, **kwargs: object) -> DoctorSchedule:
        schedule = DoctorSchedule(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(schedule)
        return schedule
