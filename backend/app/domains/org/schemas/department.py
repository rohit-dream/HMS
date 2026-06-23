"""Pydantic schemas for department management."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_DEPT_CODE_PATTERN = re.compile(r"^[A-Z0-9]{2,20}$")


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=20)
    head_staff_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not _DEPT_CODE_PATTERN.match(normalized):
            raise ValueError("Code must be 2–20 uppercase alphanumeric characters")
        return normalized


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    code: str | None = Field(default=None, min_length=2, max_length=20)
    head_staff_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not _DEPT_CODE_PATTERN.match(normalized):
            raise ValueError("Code must be 2–20 uppercase alphanumeric characters")
        return normalized


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    head_staff_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
