"""Slot generation helpers for appointment availability."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta


def schedule_day_of_week(value: date) -> int:
    """Map a calendar date to schedule day_of_week (0=Sunday … 6=Saturday)."""
    return (value.weekday() + 1) % 7


def generate_time_slots(
    window_start: time,
    window_end: time,
    slot_duration_minutes: int,
) -> list[tuple[time, time]]:
    """Split a schedule window into fixed-duration [start, end) slots."""
    slots: list[tuple[time, time]] = []
    cursor = datetime.combine(date.min, window_start)
    window_end_dt = datetime.combine(date.min, window_end)
    step = timedelta(minutes=slot_duration_minutes)

    while cursor + step <= window_end_dt:
        slot_end = cursor + step
        slots.append((cursor.time(), slot_end.time()))
        cursor = slot_end

    return slots


def slot_is_in_past(appointment_date: date, start_time: time, *, now: datetime | None = None) -> bool:
    """Return True when the slot start is before the current moment."""
    reference = now or datetime.now()
    slot_start = datetime.combine(appointment_date, start_time)
    if appointment_date < reference.date():
        return True
    if appointment_date == reference.date():
        return slot_start.time() < reference.time().replace(tzinfo=None)
    return False
