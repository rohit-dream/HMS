"""
MVP-101 — OPD end-to-end integration workflow (Sprint 9).

Exercises the full clinical vertical slice via HTTP:
patient → appointment → OPD visit → queue poll/call → consult → vitals → notes → e-Rx
→ complete → patient visit history, with walk-in path and role isolation.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from tests.helpers.appointments_api import create_appointment
from tests.helpers.opd_api import (
    auth_headers,
    confirm_appointment,
    create_patient,
    create_visit,
    provision_receptionist_with_doctor,
    start_consultation,
    visit_payload,
)
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration

VITALS_PAYLOAD = {
    "blood_pressure_systolic": 118,
    "blood_pressure_diastolic": 76,
    "pulse_rate": 80,
    "temperature": "37.0",
    "respiratory_rate": 18,
    "spo2": 99,
    "weight_kg": "64.0",
    "height_cm": "168.0",
    "notes": "Stable vitals",
}

PRESCRIPTION_PAYLOAD = {
    "notes": "Complete the full course",
    "items": [
        {
            "medicine_name": "Amoxicillin 500mg",
            "dosage": "500mg",
            "frequency": "three times daily",
            "duration": "5 days",
            "route": "oral",
            "instructions": "After meals",
            "quantity": 15,
        }
    ],
}

DIAGNOSIS_TEXT = "Acute upper respiratory tract infection"


def test_opd_appointment_to_consult_workflow_e2e(client: TestClient) -> None:
    """Sprint 9 OPD slice — appointment-linked visit through queue, consult, and history."""
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    location_id = str(ctx["location_id"])
    visit_date = (date.today() + timedelta(days=1)).isoformat()
    phone = f"98765{uuid.uuid4().int % 100000:05d}"

    patient_id = create_patient(client, headers, phone=phone, location_id=location_id)

    booked = create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        location_id=location_id,
        appointment_date=visit_date,
        start_time="09:00:00",
        end_time="09:20:00",
        appointment_type="follow_up",
        notes="OPD workflow E2E",
    )
    assert booked.status_code == status.HTTP_201_CREATED, booked.text
    appointment_id = booked.json()["data"]["id"]
    confirm_appointment(client, headers, appointment_id)

    visit_resp = client.post(
        "/api/v1/opd/visits",
        json=visit_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            location_id=location_id,
            visit_date=visit_date,
            visit_type="appointment",
            appointment_id=appointment_id,
            chief_complaint="Sore throat and mild fever",
        ),
        headers=headers,
    )
    assert visit_resp.status_code == status.HTTP_201_CREATED, visit_resp.text
    visit = visit_resp.json()["data"]
    visit_id = visit["id"]
    queue_id = visit["queue_id"]
    assert visit["status"] == "waiting"
    assert visit["visit_type"] == "appointment"
    assert visit["token_number"] == 1
    assert queue_id is not None

    poll_before = client.get(
        "/api/v1/opd/queue/poll",
        params={"doctor_id": doctor_id, "date": visit_date},
        headers=headers,
    )
    assert poll_before.status_code == status.HTTP_200_OK, poll_before.text
    poll_data = poll_before.json()["data"]
    assert poll_data["waiting_count"] >= 1
    assert poll_data["poll_interval_seconds"] == 5
    assert any(entry["opd_visit_id"] == visit_id for entry in poll_data["entries"])

    called = client.post(f"/api/v1/opd/queue/{queue_id}/call", headers=headers)
    assert called.status_code == status.HTTP_200_OK, called.text
    assert called.json()["data"]["status"] == "called"

    poll_after_call = client.get(
        "/api/v1/opd/queue/poll",
        params={"doctor_id": doctor_id, "date": visit_date},
        headers=headers,
    )
    assert poll_after_call.status_code == status.HTTP_200_OK
    assert poll_after_call.json()["data"]["current_token"] == visit["token_number"]

    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)

    forbidden_note = client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "diagnosis", "content": "Should not be allowed"},
        headers=headers,
    )
    assert forbidden_note.status_code == status.HTTP_403_FORBIDDEN

    vitals = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json=VITALS_PAYLOAD,
        headers=doctor_headers,
    )
    assert vitals.status_code == status.HTTP_201_CREATED, vitals.text
    assert vitals.json()["data"]["pulse_rate"] == 80

    examination = client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={
            "note_type": "examination",
            "content": "Mild pharyngeal erythema. Lungs clear.",
        },
        headers=doctor_headers,
    )
    assert examination.status_code == status.HTTP_201_CREATED, examination.text

    diagnosis = client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "diagnosis", "content": DIAGNOSIS_TEXT},
        headers=doctor_headers,
    )
    assert diagnosis.status_code == status.HTTP_201_CREATED, diagnosis.text

    prescription = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=doctor_headers,
    )
    assert prescription.status_code == status.HTTP_201_CREATED, prescription.text
    assert prescription.json()["data"]["items"][0]["medicine_name"] == "Amoxicillin 500mg"

    completed = client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"finalize_notes": True, "create_billing_draft": False},
        headers=doctor_headers,
    )
    assert completed.status_code == status.HTTP_200_OK, completed.text
    assert completed.json()["data"]["status"] == "completed"

    detail = client.get(f"/api/v1/opd/visits/{visit_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    detail_body = detail.json()["data"]
    assert detail_body["status"] == "completed"
    assert detail_body["vitals_count"] == 1
    assert detail_body["notes_count"] >= 2
    assert detail_body["prescriptions_count"] == 1

    history = client.get(f"/api/v1/patients/{patient_id}/visits", headers=headers)
    assert history.status_code == status.HTTP_200_OK
    history_items = history.json()["data"]
    assert any(item["id"] == visit_id for item in history_items)
    completed_visit = next(item for item in history_items if item["id"] == visit_id)
    assert completed_visit["status"] == "completed"
    assert completed_visit["chief_complaint"] == "Sore throat and mild fever"
    assert completed_visit["diagnosis"] == DIAGNOSIS_TEXT

    with session_scope() as db:
        from sqlalchemy import select

        from app.models.audit.audit_log import AuditLog

        set_rls_tenant_context(db, ctx["tenant_id"])
        audit_row = db.scalars(
            select(AuditLog).where(
                AuditLog.entity_type == "patient",
                AuditLog.entity_id == uuid.UUID(patient_id),
                AuditLog.action == "view",
            )
        ).first()
        assert audit_row is not None
        assert audit_row.audit_metadata is not None
        assert audit_row.audit_metadata.get("phi_access") is True
        assert audit_row.audit_metadata.get("resource_type") == "opd_visit"
        assert audit_row.audit_metadata.get("resource_id") == visit_id

    other = uuid.uuid4()
    with session_scope() as db:
        tenant = provision_tenant_with_role(
            db,
            slug=f"opd-e2e-{other.hex[:8]}",
            email=f"opd-e2e-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    cross_tenant = client.get(f"/api/v1/opd/visits/{visit_id}", headers=other_headers)
    assert cross_tenant.status_code == status.HTTP_404_NOT_FOUND


def test_opd_walk_in_workflow_e2e(client: TestClient) -> None:
    """Walk-in OPD visit — queue, consult, and patient visit history."""
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    location_id = str(ctx["location_id"])
    visit_date = date.today().isoformat()

    patient_id = create_patient(
        client,
        headers,
        phone=f"98765{uuid.uuid4().int % 100000:05d}",
        location_id=location_id,
    )

    visit_resp = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        location_id=location_id,
        visit_date=visit_date,
        chief_complaint="Walk-in headache",
    )
    assert visit_resp.status_code == status.HTTP_201_CREATED, visit_resp.text
    visit = visit_resp.json()["data"]
    visit_id = visit["id"]
    assert visit["visit_type"] == "walk_in"
    assert visit["queue_id"] is not None

    board = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": doctor_id, "date": visit_date},
        headers=headers,
    )
    assert board.status_code == status.HTTP_200_OK
    assert board.json()["data"]["waiting_count"] >= 1

    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)

    client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 72, "spo2": 98},
        headers=doctor_headers,
    ).raise_for_status()

    client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "diagnosis", "content": "Tension headache"},
        headers=doctor_headers,
    ).raise_for_status()

    completed = client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"finalize_notes": True, "create_billing_draft": False},
        headers=doctor_headers,
    )
    assert completed.status_code == status.HTTP_200_OK
    assert completed.json()["data"]["status"] == "completed"

    history = client.get(f"/api/v1/patients/{patient_id}/visits", headers=headers)
    assert history.status_code == status.HTTP_200_OK
    items = history.json()["data"]
    walk_in = next(item for item in items if item["id"] == visit_id)
    assert walk_in["visit_type"] == "opd"
    assert walk_in["chief_complaint"] == "Walk-in headache"
    assert walk_in["diagnosis"] == "Tension headache"
