"""
MVP-090 — Appointment end-to-end integration workflow (Sprint 8).

Exercises the full vertical slice via HTTP:
patient registration → availability → book → list → confirm → reschedule → cancel → rebook,
with tenant isolation and doctor read access.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.identity.services.rbac_service import RbacProvisioner
from app.models.core.user import User
from tests.helpers.appointments_api import (
    appointment_payload,
    auth_headers,
    create_appointment,
    create_patient,
    provision_receptionist_with_doctor,
)
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def test_appointment_lifecycle_workflow_e2e(client: TestClient) -> None:
    """Sprint 8 appointment slice — book, manage status, reschedule, cancel, and rebook."""
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    location_id = str(ctx["location_id"])
    appt_date = (date.today() + timedelta(days=3)).isoformat()
    phone = f"98765{uuid.uuid4().int % 100000:05d}"

    patient_id = create_patient(client, headers, phone=phone, location_id=location_id)

    availability_before = client.get(
        "/api/v1/appointments/availability",
        params={"doctor_id": doctor_id, "date": appt_date},
        headers=headers,
    )
    assert availability_before.status_code == status.HTTP_200_OK, availability_before.text
    slots_before = {
        slot["start_time"]: slot["available"]
        for slot in availability_before.json()["data"]["slots"]
    }
    assert slots_before.get("09:00:00") is True

    book = create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        location_id=location_id,
        appointment_date=appt_date,
        start_time="09:00:00",
        end_time="09:20:00",
        appointment_type="follow_up",
        notes="Annual check-up",
    )
    assert book.status_code == status.HTTP_201_CREATED, book.text
    booked = book.json()["data"]
    appointment_id = booked["id"]
    assert booked["status"] == "scheduled"
    assert booked["patient_name"] == "Anita Sharma"
    assert booked["appointment_type"] == "follow_up"

    availability_after_book = client.get(
        "/api/v1/appointments/availability",
        params={"doctor_id": doctor_id, "date": appt_date},
        headers=headers,
    )
    slots_after_book = {
        slot["start_time"]: slot["available"]
        for slot in availability_after_book.json()["data"]["slots"]
    }
    assert slots_after_book["09:00:00"] is False
    assert slots_after_book["09:20:00"] is True

    listing = client.get(
        "/api/v1/appointments",
        params={
            "doctor_id": doctor_id,
            "appointment_date": appt_date,
            "status": "scheduled",
        },
        headers=headers,
    )
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == appointment_id for item in listing.json()["data"])

    detail = client.get(f"/api/v1/appointments/{appointment_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["notes"] == "Annual check-up"

    confirm = client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)
    assert confirm.status_code == status.HTTP_200_OK
    assert confirm.json()["data"]["status"] == "confirmed"

    reschedule = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={
            "appointment_date": appt_date,
            "start_time": "09:20:00",
            "end_time": "09:40:00",
            "notes": "Rescheduled to next slot",
        },
        headers=headers,
    )
    assert reschedule.status_code == status.HTTP_200_OK, reschedule.text
    assert reschedule.json()["data"]["start_time"] == "09:20:00"
    assert reschedule.json()["data"]["notes"] == "Rescheduled to next slot"

    slots_after_move = client.get(
        "/api/v1/appointments/availability",
        params={"doctor_id": doctor_id, "date": appt_date},
        headers=headers,
    ).json()["data"]["slots"]
    moved_slots = {slot["start_time"]: slot["available"] for slot in slots_after_move}
    assert moved_slots["09:00:00"] is True
    assert moved_slots["09:20:00"] is False

    cancel = client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"cancelled_reason": "Patient requested cancellation"},
        headers=headers,
    )
    assert cancel.status_code == status.HTTP_200_OK
    assert cancel.json()["data"]["status"] == "cancelled"

    slots_after_cancel = client.get(
        "/api/v1/appointments/availability",
        params={"doctor_id": doctor_id, "date": appt_date},
        headers=headers,
    ).json()["data"]["slots"]
    freed_slots = {slot["start_time"]: slot["available"] for slot in slots_after_cancel}
    assert freed_slots["09:20:00"] is True

    rebook = client.post(
        "/api/v1/appointments",
        json=appointment_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            location_id=location_id,
            appointment_date=appt_date,
            start_time="09:20:00",
            end_time="09:40:00",
            appointment_type="new",
        ),
        headers=headers,
    )
    assert rebook.status_code == status.HTTP_201_CREATED, rebook.text

    other_tenant = uuid.uuid4()
    with session_scope() as db:
        other = provision_tenant_with_role(
            db,
            slug=f"appt-iso-{other_tenant.hex[:8]}",
            email=f"appt-iso-{other_tenant.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, other["slug"], other["email"])
    cross_tenant = client.get(f"/api/v1/appointments/{appointment_id}", headers=other_headers)
    assert cross_tenant.status_code == status.HTTP_404_NOT_FOUND


def test_doctor_can_read_tenant_appointments(client: TestClient) -> None:
    """Doctors in the same tenant can list and view appointments but cannot book."""
    ctx = provision_receptionist_with_doctor()
    receptionist_headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    appt_date = (date.today() + timedelta(days=4)).isoformat()

    patient_id = create_patient(
        client,
        receptionist_headers,
        phone=f"98765{uuid.uuid4().int % 100000:05d}",
    )
    created = create_appointment(
        client,
        receptionist_headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appt_date,
        start_time="10:00:00",
        end_time="10:20:00",
    )
    assert created.status_code == status.HTTP_201_CREATED
    appointment_id = created.json()["data"]["id"]

    doctor_email = f"doc-{uuid.uuid4().hex[:8]}@example.com"
    with session_scope() as db:
        set_rls_tenant_context(db, ctx["tenant_id"])
        doctor_user = User(
            tenant_id=ctx["tenant_id"],
            email=doctor_email,
            password_hash=hash_password("SecurePass@123"),
            first_name="Vikram",
            last_name="Patel",
            status="active",
        )
        db.add(doctor_user)
        db.flush()
        RbacProvisioner(db).assign_role(ctx["tenant_id"], doctor_user.id, "doctor")
        db.commit()

    doctor_headers = auth_headers(client, ctx["slug"], doctor_email)
    listing = client.get(
        "/api/v1/appointments",
        params={"doctor_id": doctor_id, "appointment_date": appt_date},
        headers=doctor_headers,
    )
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == appointment_id for item in listing.json()["data"])

    detail = client.get(f"/api/v1/appointments/{appointment_id}", headers=doctor_headers)
    assert detail.status_code == status.HTTP_200_OK

    forbidden = client.post(
        "/api/v1/appointments",
        json=appointment_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appt_date,
            start_time="10:20:00",
            end_time="10:40:00",
        ),
        headers=doctor_headers,
    )
    assert forbidden.status_code == status.HTTP_403_FORBIDDEN
