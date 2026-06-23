"""Unit tests — doctor schedule schemas and overlap logic."""

from __future__ import annotations

from datetime import time

import pytest
from pydantic import ValidationError

from app.domains.org.schemas.doctor_schedule import (
    DoctorScheduleCreateRequest,
    DoctorScheduleUpdateRequest,
    times_overlap,
)


def test_end_time_must_be_after_start_time() -> None:
    with pytest.raises(ValidationError):
        DoctorScheduleCreateRequest(
            day_of_week=1,
            start_time=time(13, 0),
            end_time=time(9, 0),
            slot_duration_minutes=20,
        )


def test_slot_duration_must_be_allowed_value() -> None:
    with pytest.raises(ValidationError):
        DoctorScheduleCreateRequest(
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=25,
        )


def test_day_of_week_must_be_between_0_and_6() -> None:
    with pytest.raises(ValidationError):
        DoctorScheduleCreateRequest(
            day_of_week=7,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
        )


def test_times_overlap_detects_intersection() -> None:
    assert times_overlap(time(9, 0), time(12, 0), time(11, 0), time(14, 0)) is True
    assert times_overlap(time(9, 0), time(12, 0), time(12, 0), time(14, 0)) is False
    assert times_overlap(time(9, 0), time(12, 0), time(7, 0), time(9, 0)) is False


def test_schedule_update_allows_partial_fields() -> None:
    payload = DoctorScheduleUpdateRequest(is_active=False)
    assert payload.is_active is False
