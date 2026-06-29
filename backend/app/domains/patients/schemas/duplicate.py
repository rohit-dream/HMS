"""Pydantic schemas for duplicate patient detection."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

DuplicateMatchReason = Literal["phone", "name"]


class DuplicateMatchResponse(BaseModel):
    patient_id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str | None = None
    phone: str
    date_of_birth: date
    match_reasons: list[DuplicateMatchReason] = Field(min_length=1)


class DuplicateCheckResponse(BaseModel):
    has_duplicates: bool
    matches: list[DuplicateMatchResponse] = Field(default_factory=list)
