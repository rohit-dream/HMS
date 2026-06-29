"""Unit tests — duplicate patient detection schemas."""

from __future__ import annotations

import uuid
from datetime import date

from app.domains.patients.schemas.duplicate import DuplicateCheckResponse, DuplicateMatchResponse


def test_duplicate_check_response_empty() -> None:
    result = DuplicateCheckResponse(has_duplicates=False, matches=[])
    assert result.has_duplicates is False
    assert result.matches == []


def test_duplicate_match_requires_reasons() -> None:
    match = DuplicateMatchResponse(
        patient_id=uuid.uuid4(),
        mrn="MRN-2026-00001",
        first_name="Anita",
        last_name="Sharma",
        phone="9876543210",
        date_of_birth=date(1990, 1, 1),
        match_reasons=["phone"],
    )
    assert match.match_reasons == ["phone"]
