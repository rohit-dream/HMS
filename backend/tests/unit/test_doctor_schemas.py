"""Unit tests — doctor request schemas."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domains.org.schemas.doctor import DoctorCreateRequest, DoctorUpdateRequest


def test_consultation_fee_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        DoctorCreateRequest(
            staff_id=uuid.uuid4(),
            specialization="Cardiology",
            consultation_fee=Decimal("-1.00"),
        )


def test_fees_quantized_to_two_decimal_places() -> None:
    payload = DoctorCreateRequest(
        staff_id=uuid.uuid4(),
        specialization="General Medicine",
        consultation_fee=Decimal("500.5"),
        follow_up_fee=Decimal("300.999"),
    )
    assert payload.consultation_fee == Decimal("500.50")
    assert payload.follow_up_fee == Decimal("301.00")


def test_doctor_update_partial_fields() -> None:
    payload = DoctorUpdateRequest(is_available=False)
    assert payload.is_available is False
