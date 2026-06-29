"""Unit tests — appointment conflict detection helpers."""

from __future__ import annotations

import uuid
from datetime import date, time
from unittest.mock import MagicMock

from app.domains.clinical.repositories.appointment_repository import AppointmentRepository


def test_has_active_slot_conflict_returns_true_when_slot_taken() -> None:
    repo = AppointmentRepository(MagicMock(), uuid.uuid4())
    taken = MagicMock()
    taken.start_time = time(9, 0)
    repo.db.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=taken)))

    assert repo.has_active_slot_conflict(
        doctor_id=uuid.uuid4(),
        appointment_date=date(2026, 6, 20),
        start_time=time(9, 0),
    )


def test_has_active_slot_conflict_returns_false_when_slot_free() -> None:
    repo = AppointmentRepository(MagicMock(), uuid.uuid4())
    repo.db.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))

    assert not repo.has_active_slot_conflict(
        doctor_id=uuid.uuid4(),
        appointment_date=date(2026, 6, 20),
        start_time=time(9, 20),
    )
