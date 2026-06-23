"""Pydantic schemas for staff management."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

StaffStatus = Literal["active", "on_leave", "terminated"]
VALID_STAFF_STATUSES = frozenset({"active", "on_leave", "terminated"})


class StaffCreateRequest(BaseModel):
    employee_code: str = Field(min_length=1, max_length=20)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    department_id: uuid.UUID | None = None
    designation: str | None = Field(default=None, max_length=100)
    joining_date: date
    leaving_date: date | None = None
    status: StaffStatus = "active"
    location_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None

    @field_validator("employee_code")
    @classmethod
    def normalize_employee_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_STAFF_STATUSES:
            raise ValueError("status must be active, on_leave, or terminated")
        return value


class StaffUpdateRequest(BaseModel):
    employee_code: str | None = Field(default=None, min_length=1, max_length=20)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    department_id: uuid.UUID | None = None
    designation: str | None = Field(default=None, max_length=100)
    joining_date: date | None = None
    leaving_date: date | None = None
    status: StaffStatus | None = None
    location_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None

    @field_validator("employee_code")
    @classmethod
    def normalize_employee_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_STAFF_STATUSES:
            raise ValueError("status must be active, on_leave, or terminated")
        return value


class StaffResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    department_id: uuid.UUID | None = None
    department_name: str | None = None
    designation: str | None = None
    status: str
    joining_date: date
    leaving_date: date | None = None
    location_id: uuid.UUID | None = None
    is_doctor: bool = False
    user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
