"""Pydantic schemas for patient allergies."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

AllergySeverity = Literal["mild", "moderate", "severe"]
VALID_ALLERGY_SEVERITIES = frozenset({"mild", "moderate", "severe"})


class AllergyCreateRequest(BaseModel):
    allergen: str = Field(min_length=1, max_length=255)
    severity: AllergySeverity
    reaction: str | None = None
    onset_date: date | None = None
    is_active: bool = True

    @field_validator("allergen")
    @classmethod
    def strip_allergen(cls, value: str) -> str:
        return value.strip()

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        if value not in VALID_ALLERGY_SEVERITIES:
            raise ValueError("severity must be mild, moderate, or severe")
        return value


class AllergyResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    allergen: str
    severity: str
    reaction: str | None = None
    onset_date: date | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
