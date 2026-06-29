"""Integration tests — MVP-094 OPD vitals and clinical notes API."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.opd_api import (
    auth_headers,
    create_patient,
    create_visit,
    provision_receptionist_with_doctor,
    start_consultation,
)
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration

VITALS_PAYLOAD = {
    "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 80,
    "pulse_rate": 78,
    "temperature": "37.2",
    "respiratory_rate": 16,
    "spo2": 98,
    "weight_kg": "62.5",
    "height_cm": "165.0",
    "notes": "Patient appears alert",
}


def test_record_and_list_vitals_with_bmi(client: TestClient) -> None:
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

    recorded = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json=VITALS_PAYLOAD,
        headers=doctor_headers,
    )
    assert recorded.status_code == status.HTTP_201_CREATED, recorded.text
    data = recorded.json()["data"]
    assert data["pulse_rate"] == 78
    assert Decimal(str(data["bmi"])) == Decimal("23.0")
    assert data["temperature_unit"] == "celsius"
    assert data["recorded_by_user_id"] is not None

    listing = client.get(f"/api/v1/opd/visits/{visit_id}/vitals", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.json()["data"]) == 1


def test_create_and_list_clinical_notes(client: TestClient) -> None:
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
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={
            "note_type": "examination",
            "content": "Chest clear on auscultation. No wheeze.",
        },
        headers=doctor_headers,
    )
    assert created.status_code == status.HTTP_201_CREATED, created.text
    note = created.json()["data"]
    assert note["note_type"] == "examination"
    assert note["is_final"] is False

    filtered = client.get(
        f"/api/v1/opd/visits/{visit_id}/notes",
        params={"note_type": "examination"},
        headers=headers,
    )
    assert filtered.status_code == status.HTTP_200_OK
    assert len(filtered.json()["data"]) == 1

    diagnosis = client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "diagnosis", "content": "Upper respiratory tract infection"},
        headers=doctor_headers,
    )
    assert diagnosis.status_code == status.HTTP_201_CREATED

    all_notes = client.get(f"/api/v1/opd/visits/{visit_id}/notes", headers=headers)
    assert len(all_notes.json()["data"]) == 2


def test_vitals_on_completed_visit_returns_409(client: TestClient) -> None:
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
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 80},
        headers=doctor_headers,
    )
    assert blocked.status_code == status.HTTP_409_CONFLICT


def test_notes_on_completed_visit_returns_409(client: TestClient) -> None:
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
    client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"create_billing_draft": False},
        headers=doctor_headers,
    )

    blocked = client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "general", "content": "Late note"},
        headers=doctor_headers,
    )
    assert blocked.status_code == status.HTTP_409_CONFLICT


def test_receptionist_cannot_record_vitals(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    resp = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 80},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_cross_tenant_vitals_returns_404(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    other = uuid.uuid4()
    with session_scope() as db:
        tenant = provision_tenant_with_role(
            db,
            slug=f"vitals-iso-{other.hex[:8]}",
            email=f"vitals-iso-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    resp = client.get(f"/api/v1/opd/visits/{visit_id}/vitals", headers=other_headers)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_cross_tenant_notes_returns_404(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    other = uuid.uuid4()
    with session_scope() as db:
        tenant = provision_tenant_with_role(
            db,
            slug=f"notes-iso-{other.hex[:8]}",
            email=f"notes-iso-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    resp = client.get(f"/api/v1/opd/visits/{visit_id}/notes", headers=other_headers)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_receptionist_cannot_create_notes(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    resp = client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "general", "content": "Unauthorized note"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_empty_vitals_payload_returns_422(client: TestClient) -> None:
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

    resp = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={},
        headers=doctor_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_out_of_range_pulse_returns_422(client: TestClient) -> None:
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

    resp = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 300},
        headers=doctor_headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_diagnosis_note_with_icd_fields(client: TestClient) -> None:
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
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={
            "note_type": "diagnosis",
            "content": "Acute upper respiratory infection",
            "icd_code": "J06.9",
            "icd_description": "Acute upper respiratory infection, unspecified",
        },
        headers=doctor_headers,
    )
    assert created.status_code == status.HTTP_201_CREATED, created.text
    note = created.json()["data"]
    assert note["icd_code"] == "J06.9"
    assert note["icd_description"] == "Acute upper respiratory infection, unspecified"


def test_vitals_list_ordered_by_recorded_at_desc(client: TestClient) -> None:
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

    first = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 70},
        headers=doctor_headers,
    )
    assert first.status_code == status.HTTP_201_CREATED
    second = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 80},
        headers=doctor_headers,
    )
    assert second.status_code == status.HTTP_201_CREATED

    listing = client.get(f"/api/v1/opd/visits/{visit_id}/vitals", headers=headers)
    pulses = [row["pulse_rate"] for row in listing.json()["data"]]
    assert pulses == [80, 70]


def test_complete_visit_finalizes_notes(client: TestClient) -> None:
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

    client.post(
        f"/api/v1/opd/visits/{visit_id}/notes",
        json={"note_type": "plan", "content": "Rest and fluids"},
        headers=doctor_headers,
    )

    completed = client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"finalize_notes": True, "create_billing_draft": False},
        headers=doctor_headers,
    )
    assert completed.status_code == status.HTTP_200_OK

    notes = client.get(f"/api/v1/opd/visits/{visit_id}/notes", headers=headers)
    assert all(note["is_final"] for note in notes.json()["data"])
