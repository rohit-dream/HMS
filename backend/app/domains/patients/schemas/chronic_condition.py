"""Pydantic schemas for patient chronic conditions (JSONB on core.patients)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ConditionStatus = Literal["active", "resolved", "inactive"]
VALID_CONDITION_STATUSES = frozenset({"active", "resolved", "inactive"})


class ChronicConditionCreateRequest(BaseModel):
    condition_name: str = Field(min_length=1, max_length=255)
    icd_code: str | None = Field(default=None, max_length=20)
    diagnosed_date: date | None = None
    status: ConditionStatus = "active"
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("condition_name")
    @classmethod
    def strip_condition_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in VALID_CONDITION_STATUSES:
            raise ValueError("status must be active, resolved, or inactive")
        return value

    @field_validator("diagnosed_date")
    @classmethod
    def validate_diagnosed_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("diagnosed_date cannot be in the future")
        return value


class ChronicConditionResponse(BaseModel):
    id: uuid.UUID
    condition_name: str
    icd_code: str | None = None
    diagnosed_date: date | None = None
    status: str
    notes: str | None = None
    recorded_at: datetime
