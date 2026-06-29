"""Pydantic schemas for appointment CRUD."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

AppointmentType = Literal["new", "follow_up", "emergency"]
AppointmentStatus = Literal["scheduled", "confirmed", "completed", "cancelled", "no_show"]

VALID_APPOINTMENT_TYPES = frozenset({"new", "follow_up", "emergency"})
VALID_APPOINTMENT_STATUSES = frozenset(
    {"scheduled", "confirmed", "completed", "cancelled", "no_show"}
)
TERMINAL_STATUSES = frozenset({"completed", "cancelled", "no_show"})


class AppointmentCreateRequest(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    location_id: uuid.UUID | None = None
    appointment_date: date
    start_time: time
    end_time: time
    appointment_type: AppointmentType
    is_walk_in: bool = False
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("appointment_type")
    @classmethod
    def validate_appointment_type(cls, value: str) -> str:
        if value not in VALID_APPOINTMENT_TYPES:
            raise ValueError("appointment_type must be new, follow_up, or emergency")
        return value

    @model_validator(mode="after")
    def validate_times(self) -> AppointmentCreateRequest:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AppointmentUpdateRequest(BaseModel):
    location_id: uuid.UUID | None = None
    appointment_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    appointment_type: AppointmentType | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("appointment_type")
    @classmethod
    def validate_appointment_type(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_APPOINTMENT_TYPES:
            raise ValueError("appointment_type must be new, follow_up, or emergency")
        return value

    @model_validator(mode="after")
    def validate_times(self) -> AppointmentUpdateRequest:
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class AppointmentCancelRequest(BaseModel):
    cancelled_reason: str = Field(min_length=1, max_length=500)

    @field_validator("cancelled_reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("cancelled_reason is required")
        return trimmed


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    doctor_id: uuid.UUID
    doctor_name: str
    location_id: uuid.UUID | None = None
    appointment_date: date
    start_time: time
    end_time: time
    appointment_type: str
    status: str
    is_walk_in: bool
    notes: str | None = None
    cancelled_reason: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class AvailabilitySlotResponse(BaseModel):
    start_time: time
    end_time: time
    available: bool


class AvailabilityResponse(BaseModel):
    doctor_id: uuid.UUID
    date: date
    slots: list[AvailabilitySlotResponse]
