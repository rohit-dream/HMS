"""
MVP-102 — Gate G3 end-to-end clinical workflow (Sprint 9).

Gate criteria (09_MVP_SPRINT_PLAN_V2):
Patient → appointment → OPD consult → e-Rx

Sprint 9 Definition of Done:
- Walk-in and appointment both create visits
- Queue board updates via polling
- Doctor completes consult with vitals + e-Rx
- Visit appears on patient history
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
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "pulse_rate": 76,
    "temperature": "36.8",
    "spo2": 98,
}

PRESCRIPTION_PAYLOAD = {
    "items": [
        {
            "medicine_name": "Azithromycin 500mg",
            "dosage": "500mg",
            "frequency": "once daily",
            "duration": "3 days",
            "route": "oral",
        }
    ],
}

DIAGNOSIS_TEXT = "Acute bronchitis"


def test_g3_clinical_workflow_e2e(client: TestClient) -> None:
    """
    Gate G3 — full Sprint 9 clinical path:
    register patient → search → walk-in + appointment visits → queue → consult → e-Rx → history.
    """
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    doctor_id = str(ctx["doctor_id"])
    location_id = str(ctx["location_id"])
    visit_date = (date.today() + timedelta(days=1)).isoformat()
    phone = f"98765{uuid.uuid4().int % 100000:05d}"

    created = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Anita",
            "last_name": "Sharma",
            "date_of_birth": "1985-03-15",
            "gender": "female",
            "phone": phone,
            "data_processing_consent": True,
            "consent_method": "written",
            "location_id": location_id,
        },
        headers=headers,
    )
    assert created.status_code == status.HTTP_201_CREATED, created.text
    patient = created.json()["data"]
    patient_id = patient["id"]
    mrn = patient["mrn"]
    assert mrn.startswith("MRN-")

    search = client.get("/api/v1/patients", params={"search": phone}, headers=headers)
    assert search.status_code == status.HTTP_200_OK
    assert any(item["id"] == patient_id for item in search.json()["data"])

    booked = create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=doctor_id,
        location_id=location_id,
        appointment_date=visit_date,
        start_time="09:00:00",
        end_time="09:20:00",
    )
    assert booked.status_code == status.HTTP_201_CREATED, booked.text
    appointment_id = booked.json()["data"]["id"]
    confirm_appointment(client, headers, appointment_id)

    appointment_visit_resp = client.post(
        "/api/v1/opd/visits",
        json=visit_payload(
            patient_id=patient_id,
            doctor_id=doctor_id,
            location_id=location_id,
            visit_date=visit_date,
            visit_type="appointment",
            appointment_id=appointment_id,
            chief_complaint="Persistent cough",
        ),
        headers=headers,
    )
    assert appointment_visit_resp.status_code == status.HTTP_201_CREATED, appointment_visit_resp.text
    appointment_visit = appointment_visit_resp.json()["data"]
    visit_id = appointment_visit["id"]
    queue_id = appointment_visit["queue_id"]
    assert appointment_visit["visit_type"] == "appointment"
    assert appointment_visit["token_number"] == 1

    walk_in_patient_id = create_patient(
        client,
        headers,
        phone=f"98765{uuid.uuid4().int % 100000:05d}",
        location_id=location_id,
    )
    walk_in_resp = create_visit(
        client,
        headers,
        patient_id=walk_in_patient_id,
        doctor_id=doctor_id,
        location_id=location_id,
        visit_date=visit_date,
        chief_complaint="Walk-in fever",
    )
    assert walk_in_resp.status_code == status.HTTP_201_CREATED, walk_in_resp.text
    walk_in_visit = walk_in_resp.json()["data"]
    assert walk_in_visit["visit_type"] == "walk_in"
    assert walk_in_visit["token_number"] == 2

    board = client.get(
        "/api/v1/opd/queue",
        params={"doctor_id": doctor_id, "date": visit_date},
        headers=headers,
    )
    assert board.status_code == status.HTTP_200_OK, board.text
    board_data = board.json()["data"]
    assert board_data["waiting_count"] == 2
    board_tokens = [entry["token_number"] for entry in board_data["entries"]]
    assert board_tokens == [1, 2]

    poll = client.get(
        "/api/v1/opd/queue/poll",
        params={"doctor_id": doctor_id, "date": visit_date},
        headers=headers,
    )
    assert poll.status_code == status.HTTP_200_OK, poll.text
    poll_body = poll.json()["data"]
    assert poll_body["poll_interval_seconds"] == 5
    assert poll_body["waiting_count"] == 2
    etag = poll.headers.get("etag")
    assert etag

    unchanged = client.get(
        "/api/v1/opd/queue/poll",
        params={"doctor_id": doctor_id, "date": visit_date},
        headers={**headers, "If-None-Match": etag},
    )
    assert unchanged.status_code == status.HTTP_304_NOT_MODIFIED

    called = client.post(f"/api/v1/opd/queue/{queue_id}/call", headers=headers)
    assert called.status_code == status.HTTP_200_OK, called.text

    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)

    vitals = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json=VITALS_PAYLOAD,
        headers=doctor_headers,
    )
    assert vitals.status_code == status.HTTP_201_CREATED, vitals.text

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
    rx = prescription.json()["data"]
    assert rx["prescription_number"].startswith("RX-")
    assert rx["items"][0]["medicine_name"] == "Azithromycin 500mg"

    completed = client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"finalize_notes": True, "create_billing_draft": False},
        headers=doctor_headers,
    )
    assert completed.status_code == status.HTTP_200_OK, completed.text
    assert completed.json()["data"]["status"] == "completed"

    history = client.get(f"/api/v1/patients/{patient_id}/visits", headers=headers)
    assert history.status_code == status.HTTP_200_OK
    history_row = next(item for item in history.json()["data"] if item["id"] == visit_id)
    assert history_row["status"] == "completed"
    assert history_row["reference_number"] == appointment_visit["visit_number"]
    assert history_row["diagnosis"] == DIAGNOSIS_TEXT
    assert history_row["chief_complaint"] == "Persistent cough"

    profile = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert profile.status_code == status.HTTP_200_OK
    assert profile.json()["data"]["mrn"] == mrn

    other = uuid.uuid4()
    with session_scope() as db:
        tenant = provision_tenant_with_role(
            db,
            slug=f"g3-iso-{other.hex[:8]}",
            email=f"g3-iso-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    assert (
        client.get(f"/api/v1/patients/{patient_id}", headers=other_headers).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert (
        client.get(f"/api/v1/opd/visits/{visit_id}", headers=other_headers).status_code
        == status.HTTP_404_NOT_FOUND
    )

    with session_scope() as db:
        from sqlalchemy import select

        from app.models.audit.audit_log import AuditLog

        set_rls_tenant_context(db, ctx["tenant_id"])
        phi_row = db.scalars(
            select(AuditLog).where(
                AuditLog.entity_type == "patient",
                AuditLog.entity_id == uuid.UUID(patient_id),
                AuditLog.action == "view",
            )
        ).first()
        assert phi_row is not None
        assert phi_row.audit_metadata.get("phi_access") is True


def test_g3_receptionist_cannot_prescribe(client: TestClient) -> None:
    """Gate G3 RBAC — receptionist may manage queue but cannot write prescriptions."""
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(
        client,
        headers,
        phone=f"98765{uuid.uuid4().int % 100000:05d}",
    )
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]
    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)

    blocked = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=headers,
    )
    assert blocked.status_code == status.HTTP_403_FORBIDDEN

    allowed = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=doctor_headers,
    )
    assert allowed.status_code == status.HTTP_201_CREATED, allowed.text
