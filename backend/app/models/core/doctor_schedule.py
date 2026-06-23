"""core.doctor_schedules — weekly doctor availability slots."""

from __future__ import annotations

import uuid
from datetime import time

from sqlalchemy import Boolean, Integer, SmallInteger, Time
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class DoctorSchedule(TenantAuditableEntity):
    __tablename__ = "doctor_schedules"
    __table_args__ = {"schema": "core"}

    doctor_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_patients_per_slot: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    location_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
