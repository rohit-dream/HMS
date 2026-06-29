"""MVP-052 — OPD schema unit tests."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.domains.clinical.schemas.opd.prescription import OpdPrescriptionCreateRequest
from app.domains.clinical.schemas.opd.queue import OpdQueueUpdateRequest
from app.domains.clinical.schemas.opd.vitals import OpdVitalsCreateRequest
from app.domains.clinical.schemas.opd.visit import OpdVisitCreateRequest


def test_opd_visit_create_requires_patient_and_doctor() -> None:
    with pytest.raises(ValidationError):
        OpdVisitCreateRequest.model_validate({})


def test_opd_visit_create_accepts_walk_in_defaults() -> None:
    payload = OpdVisitCreateRequest(
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        visit_date=date.today(),
    )
    assert payload.visit_type == "walk_in"
    assert payload.add_to_queue is True


def test_opd_vitals_rejects_out_of_range_pulse() -> None:
    with pytest.raises(ValidationError):
        OpdVitalsCreateRequest(pulse_rate=500)


def test_opd_prescription_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        OpdPrescriptionCreateRequest(items=[])


def test_opd_queue_update_position_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        OpdQueueUpdateRequest(position=0)
