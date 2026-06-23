"""Unit tests — staff request schemas."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.domains.org.schemas.staff import StaffCreateRequest, StaffUpdateRequest


def test_employee_code_normalized_to_uppercase() -> None:
    payload = StaffCreateRequest(
        employee_code="emp-42",
        first_name="Jane",
        last_name="Doe",
        joining_date=date(2024, 1, 1),
    )
    assert payload.employee_code == "EMP-42"


def test_staff_status_must_be_valid() -> None:
    with pytest.raises(ValidationError):
        StaffCreateRequest(
            employee_code="EMP-1",
            first_name="Jane",
            last_name="Doe",
            joining_date=date(2024, 1, 1),
            status="invalid",  # type: ignore[arg-type]
        )


def test_staff_update_allows_on_leave() -> None:
    payload = StaffUpdateRequest(status="on_leave")
    assert payload.status == "on_leave"
