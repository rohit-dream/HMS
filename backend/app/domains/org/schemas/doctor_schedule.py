"""Pydantic schemas for doctor weekly schedules."""

from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_SLOT_DURATIONS = frozenset({10, 15, 20, 30, 60})


def times_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """Return True when two half-open time ranges [start, end) overlap."""
    return start_a < end_b and end_a > start_b


class DoctorScheduleCreateRequest(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(gt=0)
    max_patients_per_slot: int = Field(default=1, gt=0)
    location_id: uuid.UUID | None = None
    is_active: bool = True

    @field_validator("slot_duration_minutes")
    @classmethod
    def validate_slot_duration(cls, value: int) -> int:
        if value not in ALLOWED_SLOT_DURATIONS:
            allowed = ", ".join(str(v) for v in sorted(ALLOWED_SLOT_DURATIONS))
            raise ValueError(f"slot_duration_minutes must be one of: {allowed}")
        return value

    @model_validator(mode="after")
    def validate_time_window(self) -> Self:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class DoctorScheduleUpdateRequest(BaseModel):
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(default=None, gt=0)
    max_patients_per_slot: int | None = Field(default=None, gt=0)
    location_id: uuid.UUID | None = None
    is_active: bool | None = None

    @field_validator("slot_duration_minutes")
    @classmethod
    def validate_slot_duration(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value not in ALLOWED_SLOT_DURATIONS:
            allowed = ", ".join(str(v) for v in sorted(ALLOWED_SLOT_DURATIONS))
            raise ValueError(f"slot_duration_minutes must be one of: {allowed}")
        return value


class DoctorScheduleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    doctor_id: uuid.UUID
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    max_patients_per_slot: int
    location_id: uuid.UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
