"""OPD visit request/response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

OpdVisitType = Literal["walk_in", "appointment"]
OpdVisitStatus = Literal["waiting", "in_consultation", "completed", "cancelled"]
OpdQueuePriority = Literal["normal", "urgent"]


class OpdVisitCreateRequest(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    location_id: uuid.UUID | None = None
    visit_date: date | None = None
    visit_type: OpdVisitType = "walk_in"
    appointment_id: uuid.UUID | None = None
    chief_complaint: str | None = Field(default=None, max_length=2000)
    add_to_queue: bool = True
    queue_priority: OpdQueuePriority = "normal"


class OpdVisitUpdateRequest(BaseModel):
    chief_complaint: str | None = Field(default=None, max_length=2000)
    doctor_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None


class OpdVisitCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class OpdVisitStartRequest(BaseModel):
    doctor_id: uuid.UUID | None = None


class OpdVisitCompleteRequest(BaseModel):
    finalize_notes: bool = True
    create_billing_draft: bool = True
    follow_up_notes: str | None = Field(default=None, max_length=2000)


class OpdVisitResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    visit_number: str
    patient_id: uuid.UUID
    patient_name: str | None = None
    patient_mrn: str | None = None
    doctor_id: uuid.UUID
    doctor_name: str | None = None
    appointment_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    location_name: str | None = None
    visit_date: date
    visit_type: OpdVisitType
    status: OpdVisitStatus
    token_number: int | None = None
    chief_complaint: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    queue_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class OpdVisitDetailResponse(OpdVisitResponse):
    vitals_count: int = 0
    notes_count: int = 0
    prescriptions_count: int = 0
    latest_vitals: OpdVitalsResponse | None = None
    queue: OpdQueueEntryResponse | None = None


class OpdVisitCompleteResponse(BaseModel):
    id: uuid.UUID
    status: OpdVisitStatus
    completed_at: datetime
    billing_invoice_id: uuid.UUID | None = None
