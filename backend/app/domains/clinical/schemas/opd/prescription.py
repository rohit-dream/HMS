"""OPD prescription request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

OpdPrescriptionStatus = Literal["active", "dispensed", "partially_dispensed", "cancelled"]
MedicineRoute = Literal["oral", "topical", "iv", "im", "sc", "inhalation", "other"]


class OpdPrescriptionItemCreateRequest(BaseModel):
    medicine_id: uuid.UUID | None = None
    medicine_name: str = Field(min_length=1, max_length=255)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    duration: str = Field(min_length=1, max_length=100)
    route: MedicineRoute | None = "oral"
    instructions: str | None = Field(default=None, max_length=2000)
    quantity: int | None = Field(default=None, ge=1)


class OpdPrescriptionCreateRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)
    items: list[OpdPrescriptionItemCreateRequest] = Field(min_length=1, max_length=30)


class OpdPrescriptionItemResponse(BaseModel):
    id: uuid.UUID
    medicine_id: uuid.UUID | None = None
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    route: MedicineRoute | None = None
    instructions: str | None = None
    quantity: int | None = None


class OpdPrescriptionResponse(BaseModel):
    id: uuid.UUID
    opd_visit_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    prescription_number: str
    prescribed_at: datetime
    status: OpdPrescriptionStatus
    notes: str | None = None
    items: list[OpdPrescriptionItemResponse] = Field(default_factory=list)
