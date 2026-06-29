"""OPD clinical notes request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

OpdNoteType = Literal["examination", "diagnosis", "plan", "general"]


class OpdNoteCreateRequest(BaseModel):
    note_type: OpdNoteType
    content: str = Field(min_length=1, max_length=10000)
    icd_code: str | None = Field(default=None, max_length=10)
    icd_description: str | None = Field(default=None, max_length=255)


class OpdClinicalNoteResponse(BaseModel):
    id: uuid.UUID
    opd_visit_id: uuid.UUID
    note_type: OpdNoteType
    content: str
    icd_code: str | None = None
    icd_description: str | None = None
    is_final: bool
    created_by_user_id: uuid.UUID | None = None
    created_at: datetime
