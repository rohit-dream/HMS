"""Pydantic schemas for doctor profiles."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class DoctorCreateRequest(BaseModel):
    staff_id: uuid.UUID
    registration_number: str | None = Field(default=None, max_length=50)
    specialization: str = Field(min_length=1, max_length=150)
    qualification: str | None = Field(default=None, max_length=255)
    consultation_fee: Decimal = Field(ge=0)
    follow_up_fee: Decimal | None = Field(default=None, ge=0)
    department_id: uuid.UUID | None = None
    bio: str | None = None
    is_available: bool = True

    @field_validator("consultation_fee", "follow_up_fee")
    @classmethod
    def validate_fee_precision(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(Decimal("0.01"))


class DoctorUpdateRequest(BaseModel):
    registration_number: str | None = Field(default=None, max_length=50)
    specialization: str | None = Field(default=None, min_length=1, max_length=150)
    qualification: str | None = Field(default=None, max_length=255)
    consultation_fee: Decimal | None = Field(default=None, ge=0)
    follow_up_fee: Decimal | None = Field(default=None, ge=0)
    department_id: uuid.UUID | None = None
    bio: str | None = None
    is_available: bool | None = None

    @field_validator("consultation_fee", "follow_up_fee")
    @classmethod
    def validate_fee_precision(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return value.quantize(Decimal("0.01"))


class DoctorResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    staff_id: uuid.UUID
    first_name: str
    last_name: str
    employee_code: str
    registration_number: str | None = None
    specialization: str
    qualification: str | None = None
    consultation_fee: Decimal
    follow_up_fee: Decimal | None = None
    department_id: uuid.UUID | None = None
    department_name: str | None = None
    bio: str | None = None
    is_available: bool
    created_at: datetime
    updated_at: datetime | None = None
