"""Unit tests — OPD vitals BMI calculation."""

from __future__ import annotations

from decimal import Decimal

from app.domains.clinical.services.opd_vitals_service import calculate_bmi


def test_calculate_bmi_from_weight_and_height() -> None:
    bmi = calculate_bmi(weight_kg=Decimal("62.5"), height_cm=Decimal("165.0"))
    assert bmi == Decimal("23.0")


def test_calculate_bmi_rounds_to_one_decimal() -> None:
    bmi = calculate_bmi(weight_kg=Decimal("70"), height_cm=Decimal("175"))
    assert bmi == Decimal("22.9")
