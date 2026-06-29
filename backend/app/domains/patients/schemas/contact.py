"""Pydantic schemas for patient contacts."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    relationship: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=10, max_length=10)
    email: EmailStr | None = None
    is_emergency: bool = False
    is_primary: bool = False

    @field_validator("name", "relationship")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = value.strip()
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("phone must be exactly 10 digits")
        return digits


class ContactResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    relationship: str
    phone: str
    email: str | None = None
    is_emergency: bool
    is_primary: bool
    created_at: datetime
    updated_at: datetime | None = None
