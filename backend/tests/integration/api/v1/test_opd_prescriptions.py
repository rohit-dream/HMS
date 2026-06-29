"""Integration tests — MVP-095 OPD e-prescription API."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.opd_api import (
    auth_headers,
    create_patient,
    create_visit,
    provision_doctor_user,
    provision_receptionist_with_doctor,
    start_consultation,
)
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration

PRESCRIPTION_PAYLOAD = {
    "notes": "Take after meals",
    "items": [
        {
            "medicine_name": "Paracetamol 500mg",
            "dosage": "500mg",
            "frequency": "twice daily",
            "duration": "5 days",
            "route": "oral",
            "instructions": "After food",
            "quantity": 10,
        }
    ],
}


def test_create_list_and_get_prescription(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]
    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)

    created = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=doctor_headers,
    )
    assert created.status_code == status.HTTP_201_CREATED, created.text
    rx = created.json()["data"]
    assert rx["prescription_number"].startswith("RX-")
    assert rx["status"] == "active"
    assert len(rx["items"]) == 1
    assert rx["items"][0]["medicine_name"] == "Paracetamol 500mg"

    listing = client.get(f"/api/v1/opd/visits/{visit_id}/prescriptions", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.json()["data"]) == 1

    detail = client.get(
        f"/api/v1/opd/visits/{visit_id}/prescriptions/{rx['id']}",
        headers=headers,
    )
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["items"][0]["dosage"] == "500mg"


def test_prescription_requires_in_consultation(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]
    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)

    completed = client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"create_billing_draft": False},
        headers=doctor_headers,
    )
    assert completed.status_code == status.HTTP_200_OK

    blocked = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=doctor_headers,
    )
    assert blocked.status_code == status.HTTP_409_CONFLICT


def test_prescription_on_waiting_visit_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]
    doctor_headers = auth_headers(client, ctx["slug"], provision_doctor_user(ctx))

    blocked = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=doctor_headers,
    )
    assert blocked.status_code == status.HTTP_409_CONFLICT
    assert "consultation" in blocked.json()["errors"][0]["message"].lower()


def test_receptionist_cannot_prescribe(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]
    start_consultation(client, ctx, visit_id=visit_id)

    resp = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_cross_tenant_prescription_returns_404(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]
    doctor_headers = start_consultation(client, ctx, visit_id=visit_id)
    rx_id = client.post(
        f"/api/v1/opd/visits/{visit_id}/prescriptions",
        json=PRESCRIPTION_PAYLOAD,
        headers=doctor_headers,
    ).json()["data"]["id"]

    other = uuid.uuid4()
    with session_scope() as db:
        tenant = provision_tenant_with_role(
            db,
            slug=f"rx-iso-{other.hex[:8]}",
            email=f"rx-iso-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    resp = client.get(
        f"/api/v1/opd/visits/{visit_id}/prescriptions/{rx_id}",
        headers=other_headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
