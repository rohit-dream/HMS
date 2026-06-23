"""Unit tests — department request schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domains.org.schemas.department import DepartmentCreateRequest, DepartmentUpdateRequest


def test_department_code_normalized_to_uppercase() -> None:
    payload = DepartmentCreateRequest(name="Cardiology", code="card")
    assert payload.code == "CARD"


def test_department_code_rejects_invalid_format() -> None:
    with pytest.raises(ValidationError):
        DepartmentCreateRequest(name="Bad", code="a")


def test_department_update_code_validation() -> None:
    payload = DepartmentUpdateRequest(code="lab01")
    assert payload.code == "LAB01"
