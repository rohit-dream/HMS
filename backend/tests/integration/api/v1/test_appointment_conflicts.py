"""Integration tests — MVP-089 appointment slot conflict (409) handling."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from tests.helpers.appointments_api import (
    appointment_payload,
    assert_conflict_response,
    auth_headers,
    create_appointment,
    create_patient,
    provision_receptionist_with_doctor,
)


@pytest.fixture
def receptionist_with_doctor():
    return provision_receptionist_with_doctor()


def test_create_double_book_returns_409_with_start_time_field(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = auth_headers(client, receptionist_with_doctor["slug"], receptionist_with_doctor["email"])
    doctor_id = str(receptionist_with_doctor["doctor_id"])
    appt_date = (date.today() + timedelta(days=5)).isoformat()
    slot = {
        "appointment_date": appt_date,
        "start_time": "14:00:00",
        "end_time": "14:20:00",
    }

    patient_a = create_patient(client, headers, phone="9876543210")
    patient_b = create_patient(client, headers, phone="9876543211")

    first = create_appointment(
        client,
        headers,
        patient_id=patient_a,
        doctor_id=doctor_id,
        **slot,
    )
    assert first.status_code == status.HTTP_201_CREATED

    second = create_appointment(
        client,
        headers,
        patient_id=patient_b,
        doctor_id=doctor_id,
        **slot,
    )
    assert_conflict_response(second)


def test_reschedule_into_occupied_slot_returns_409(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = auth_headers(client, receptionist_with_doctor["slug"], receptionist_with_doctor["email"])
    doctor_id = str(receptionist_with_doctor["doctor_id"])
    appt_date = (date.today() + timedelta(days=6)).isoformat()

    patient_a = create_patient(client, headers, phone="9876543220")
    patient_b = create_patient(client, headers, phone="9876543221")

    create_appointment(
        client,
        headers,
        patient_id=patient_a,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        start_time="10:00:00",
        end_time="10:20:00",
    )
    second = create_appointment(
        client,
        headers,
        patient_id=patient_b,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        start_time="10:20:00",
        end_time="10:40:00",
    )
    appointment_b_id = second.json()["data"]["id"]

    reschedule = client.patch(
        f"/api/v1/appointments/{appointment_b_id}",
        json={
            "appointment_date": appt_date,
            "start_time": "10:00:00",
            "end_time": "10:20:00",
        },
        headers=headers,
    )
    assert_conflict_response(reschedule)


def test_confirmed_appointment_blocks_slot_on_new_booking(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = auth_headers(client, receptionist_with_doctor["slug"], receptionist_with_doctor["email"])
    doctor_id = str(receptionist_with_doctor["doctor_id"])
    appt_date = (date.today() + timedelta(days=7)).isoformat()
    slot = {
        "appointment_date": appt_date,
        "start_time": "11:00:00",
        "end_time": "11:20:00",
    }

    patient_a = create_patient(client, headers, phone="9876543230")
    patient_b = create_patient(client, headers, phone="9876543231")

    created = create_appointment(
        client,
        headers,
        patient_id=patient_a,
        doctor_id=doctor_id,
        **slot,
    )
    appointment_id = created.json()["data"]["id"]
    confirm = client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)
    assert confirm.status_code == status.HTTP_200_OK

    conflict = create_appointment(
        client,
        headers,
        patient_id=patient_b,
        doctor_id=doctor_id,
        **slot,
    )
    assert_conflict_response(conflict)


def test_cancelled_appointment_allows_rebooking_same_slot(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = auth_headers(client, receptionist_with_doctor["slug"], receptionist_with_doctor["email"])
    doctor_id = str(receptionist_with_doctor["doctor_id"])
    appt_date = (date.today() + timedelta(days=8)).isoformat()
    slot = {
        "appointment_date": appt_date,
        "start_time": "12:00:00",
        "end_time": "12:20:00",
    }

    patient_a = create_patient(client, headers, phone="9876543240")
    patient_b = create_patient(client, headers, phone="9876543241")

    created = create_appointment(
        client,
        headers,
        patient_id=patient_a,
        doctor_id=doctor_id,
        **slot,
    )
    appointment_id = created.json()["data"]["id"]
    cancel = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "Patient requested cancellation"},
        headers=headers,
    )
    assert cancel.status_code == status.HTTP_200_OK

    rebook = create_appointment(
        client,
        headers,
        patient_id=patient_b,
        doctor_id=doctor_id,
        **slot,
    )
    assert rebook.status_code == status.HTTP_201_CREATED


def test_reschedule_within_same_slot_does_not_conflict(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = auth_headers(client, receptionist_with_doctor["slug"], receptionist_with_doctor["email"])
    doctor_id = str(receptionist_with_doctor["doctor_id"])
    appt_date = (date.today() + timedelta(days=9)).isoformat()

    patient_id = create_patient(client, headers, phone="9876543250")
    created = create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        start_time="13:00:00",
        end_time="13:20:00",
        notes="Initial note",
    )
    appointment_id = created.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={"notes": "Updated note only"},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    assert update.json()["data"]["notes"] == "Updated note only"


def test_availability_marks_booked_slot_unavailable_after_create(
    client: TestClient,
    receptionist_with_doctor: dict,
) -> None:
    headers = auth_headers(client, receptionist_with_doctor["slug"], receptionist_with_doctor["email"])
    doctor_id = str(receptionist_with_doctor["doctor_id"])
    appt_date = (date.today() + timedelta(days=10)).isoformat()

    patient_id = create_patient(client, headers, phone="9876543260")
    create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        start_time="15:00:00",
        end_time="15:20:00",
    )

    availability = client.get(
        "/api/v1/appointments/availability",
        params={"doctor_id": doctor_id, "date": appt_date},
        headers=headers,
    )
    assert availability.status_code == status.HTTP_200_OK
    slots = {
        slot["start_time"]: slot["available"] for slot in availability.json()["data"]["slots"]
    }
    assert slots["15:00:00"] is False
    assert slots["15:20:00"] is True
