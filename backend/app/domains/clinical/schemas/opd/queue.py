"""OPD queue request/response schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domains.clinical.schemas.opd.visit import OpdQueuePriority, OpdVisitStatus

OpdQueueStatus = Literal["waiting", "called", "in_consultation", "completed", "skipped"]


class OpdQueueCreateRequest(BaseModel):
    opd_visit_id: uuid.UUID
    priority: OpdQueuePriority = "normal"


class OpdQueueUpdateRequest(BaseModel):
    priority: OpdQueuePriority | None = None
    position: int | None = Field(default=None, ge=1)


class OpdQueueSkipRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class OpdQueueEntryResponse(BaseModel):
    id: uuid.UUID
    opd_visit_id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str | None = None
    token_number: int
    queue_date: date
    status: OpdQueueStatus
    priority: OpdQueuePriority
    chief_complaint: str | None = None
    called_at: datetime | None = None
    visit_status: OpdVisitStatus | None = None


class OpdQueueBoardResponse(BaseModel):
    doctor_id: uuid.UUID
    queue_date: date
    current_token: int | None = None
    waiting_count: int
    entries: list[OpdQueueEntryResponse]


class OpdQueuePollResponse(OpdQueueBoardResponse):
    etag: str
    poll_interval_seconds: int = 5
    changed: bool = True
