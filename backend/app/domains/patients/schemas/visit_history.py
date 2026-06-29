"""Pydantic schemas for patient visit history."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel

VisitHistoryType = Literal["opd"]


class PatientVisitHistoryItem(BaseModel):
    id: uuid.UUID
    visit_type: VisitHistoryType
    reference_number: str
    visit_date: date
    status: str
    doctor_id: uuid.UUID
    doctor_name: str
    chief_complaint: str | None = None
    diagnosis: str | None = None
    department_name: str | None = None
