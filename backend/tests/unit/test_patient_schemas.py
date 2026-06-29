"""Unit tests — patient request/response schemas (Sprint 7)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.domains.patients.schemas.allergy import AllergyCreateRequest
from app.domains.patients.schemas.chronic_condition import ChronicConditionCreateRequest
from app.domains.patients.schemas.contact import ContactCreateRequest
from app.domains.patients.schemas.patient import PatientCreateRequest, PatientUpdateRequest


def _valid_create(**overrides: object) -> PatientCreateRequest:
    payload = {
        "first_name": "Anita",
        "last_name": "Sharma",
        "date_of_birth": date(1990, 3, 15),
        "gender": "female",
        "phone": "9876543210",
        "data_processing_consent": True,
        "consent_method": "digital",
    }
    payload.update(overrides)
    return PatientCreateRequest(**payload)  # type: ignore[arg-type]


def test_patient_create_strips_names() -> None:
    payload = _valid_create(first_name="  Anita  ", last_name="  Sharma ")
    assert payload.first_name == "Anita"
    assert payload.last_name == "Sharma"


def test_patient_create_normalizes_phone_digits() -> None:
    payload = _valid_create(phone="9876543210")
    assert payload.phone == "9876543210"


def test_patient_create_requires_ten_digit_phone() -> None:
    with pytest.raises(ValidationError):
        _valid_create(phone="12345")


def test_patient_create_rejects_future_dob() -> None:
    with pytest.raises(ValidationError):
        _valid_create(date_of_birth=date.today() + timedelta(days=1))


def test_patient_create_requires_consent_flag() -> None:
    with pytest.raises(ValidationError):
        _valid_create(data_processing_consent=False)


def test_patient_create_validates_blood_group() -> None:
    with pytest.raises(ValidationError):
        _valid_create(blood_group="Z+")


def test_patient_create_accepts_acknowledge_duplicate() -> None:
    payload = _valid_create(acknowledge_duplicate=True)
    assert payload.acknowledge_duplicate is True


def test_patient_update_allows_partial_fields() -> None:
    payload = PatientUpdateRequest(first_name="Updated")
    assert payload.first_name == "Updated"
    assert payload.phone is None


def test_allergy_create_validates_severity() -> None:
    with pytest.raises(ValidationError):
        AllergyCreateRequest(allergen="Penicillin", severity="critical")  # type: ignore[arg-type]


def test_contact_create_requires_ten_digit_phone() -> None:
    with pytest.raises(ValidationError):
        ContactCreateRequest(name="Raj", relationship="spouse", phone="123")


def test_chronic_condition_rejects_future_diagnosed_date() -> None:
    with pytest.raises(ValidationError):
        ChronicConditionCreateRequest(
            condition_name="Diabetes",
            diagnosed_date=date.today() + timedelta(days=1),
        )
