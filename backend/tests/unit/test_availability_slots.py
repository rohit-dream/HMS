"""Unit tests — appointment slot generation helpers."""

from __future__ import annotations

from datetime import date, datetime, time

from app.domains.clinical.availability_slots import (
    generate_time_slots,
    schedule_day_of_week,
    slot_is_in_past,
)


def test_schedule_day_of_week_uses_sunday_zero() -> None:
    # 2026-06-21 is Sunday
    assert schedule_day_of_week(date(2026, 6, 21)) == 0
    # 2026-06-22 is Monday
    assert schedule_day_of_week(date(2026, 6, 22)) == 1


def test_generate_time_slots_splits_window() -> None:
    slots = generate_time_slots(time(9, 0), time(10, 0), 20)
    assert slots == [(time(9, 0), time(9, 20)), (time(9, 20), time(9, 40)), (time(9, 40), time(10, 0))]


def test_slot_is_in_past_for_earlier_today() -> None:
    now = datetime(2026, 6, 22, 12, 0)
    assert slot_is_in_past(date(2026, 6, 22), time(11, 0), now=now) is True
    assert slot_is_in_past(date(2026, 6, 22), time(13, 0), now=now) is False


def test_slot_is_in_past_for_previous_day() -> None:
    now = datetime(2026, 6, 22, 12, 0)
    assert slot_is_in_past(date(2026, 6, 21), time(15, 0), now=now) is True
