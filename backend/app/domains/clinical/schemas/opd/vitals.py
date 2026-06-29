"""OPD vitals request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OpdVitalsCreateRequest(BaseModel):
    blood_pressure_systolic: int | None = Field(default=None, ge=60, le=250)
    blood_pressure_diastolic: int | None = Field(default=None, ge=40, le=150)
    pulse_rate: int | None = Field(default=None, ge=30, le=220)
    temperature: Decimal | None = Field(default=None, ge=30, le=45)
    respiratory_rate: int | None = Field(default=None, ge=5, le=60)
    spo2: int | None = Field(default=None, ge=50, le=100)
    weight_kg: Decimal | None = Field(default=None, ge=0.5, le=500)
    height_cm: Decimal | None = Field(default=None, ge=30, le=250)
    notes: str | None = Field(default=None, max_length=2000)


class OpdVitalsResponse(BaseModel):
    id: uuid.UUID
    opd_visit_id: uuid.UUID
    recorded_at: datetime
    recorded_by_user_id: uuid.UUID | None = None
    blood_pressure_systolic: int | None = None
    blood_pressure_diastolic: int | None = None
    pulse_rate: int | None = None
    temperature: Decimal | None = None
    temperature_unit: str | None = None
    respiratory_rate: int | None = None
    spo2: int | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    bmi: Decimal | None = None
    notes: str | None = None
