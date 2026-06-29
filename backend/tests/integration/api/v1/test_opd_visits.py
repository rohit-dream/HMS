"""Integration tests — MVP-092 OPD visits API."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.appointments_api import appointment_payload, create_appointment
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


def test_create_walk_in_visit_with_queue(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")

    resp = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()["data"]
    assert data["status"] == "waiting"
    assert data["visit_type"] == "walk_in"
    assert data["visit_number"].startswith("OPD-")
    assert data["token_number"] == 1
    assert data["queue_id"] is not None
    assert data["patient_name"] == "Anita Sharma"


def test_list_and_get_visit(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    created = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    )
    visit_id = created.json()["data"]["id"]

    listing = client.get(
        "/api/v1/opd/visits",
        params={"doctor_id": str(ctx["doctor_id"]), "status": "waiting"},
        headers=headers,
    )
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == visit_id for item in listing.json()["data"])

    detail = client.get(f"/api/v1/opd/visits/{visit_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    body = detail.json()["data"]
    assert body["vitals_count"] == 0
    assert body["notes_count"] == 0
    assert body["prescriptions_count"] == 0
    assert body["latest_vitals"] is None
    assert body["queue"] is not None
    assert body["queue"]["token_number"] == body["token_number"]

    with session_scope() as db:
        from sqlalchemy import select

        from app.core.database import set_rls_tenant_context
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


def test_update_visit_while_waiting(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    updated = client.patch(
        f"/api/v1/opd/visits/{visit_id}",
        json={"chief_complaint": "Updated complaint"},
        headers=headers,
    )
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json()["data"]["chief_complaint"] == "Updated complaint"


def test_create_visit_from_confirmed_appointment(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    appt_date = (date.today() + timedelta(days=2)).isoformat()
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    appointment = create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
        location_id=str(ctx["location_id"]),
        appointment_date=appt_date,
        start_time="09:00:00",
        end_time="09:20:00",
    )
    assert appointment.status_code == status.HTTP_201_CREATED
    appointment_id = appointment.json()["data"]["id"]
    confirm_appointment(client, headers, appointment_id)

    resp = client.post(
        "/api/v1/opd/visits",
        json=visit_payload(
            patient_id=patient_id,
            doctor_id=str(ctx["doctor_id"]),
            location_id=str(ctx["location_id"]),
            visit_date=appt_date,
            visit_type="appointment",
            appointment_id=appointment_id,
        ),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    assert resp.json()["data"]["appointment_id"] == appointment_id


def test_duplicate_appointment_visit_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    appt_date = (date.today() + timedelta(days=1)).isoformat()
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    appointment = create_appointment(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
        appointment_date=appt_date,
        start_time="10:00:00",
        end_time="10:20:00",
    )
    appointment_id = appointment.json()["data"]["id"]
    confirm_appointment(client, headers, appointment_id)

    payload = visit_payload(
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
        visit_date=appt_date,
        visit_type="appointment",
        appointment_id=appointment_id,
    )
    first = client.post("/api/v1/opd/visits", json=payload, headers=headers)
    assert first.status_code == status.HTTP_201_CREATED

    second = client.post("/api/v1/opd/visits", json=payload, headers=headers)
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["errors"][0]["field"] == "appointment_id"


def test_visit_lifecycle_start_complete(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    doctor_email = f"doc-{uuid.uuid4().hex[:8]}@example.com"
    with session_scope() as db:
        from app.core.database import set_rls_tenant_context
        from app.domains.identity.services.rbac_service import RbacProvisioner
        from app.models.core.user import User

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
    started = client.post(f"/api/v1/opd/visits/{visit_id}/start", json={}, headers=doctor_headers)
    assert started.status_code == status.HTTP_200_OK
    assert started.json()["data"]["status"] == "in_consultation"
    assert started.json()["data"]["started_at"] is not None

    completed = client.post(
        f"/api/v1/opd/visits/{visit_id}/complete",
        json={"finalize_notes": True, "create_billing_draft": False},
        headers=doctor_headers,
    )
    assert completed.status_code == status.HTTP_200_OK
    assert completed.json()["data"]["status"] == "completed"
    assert completed.json()["data"]["billing_invoice_id"] is None


def test_cancel_visit(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    cancelled = client.post(
        f"/api/v1/opd/visits/{visit_id}/cancel",
        json={"reason": "Patient did not arrive"},
        headers=headers,
    )
    assert cancelled.status_code == status.HTTP_200_OK
    assert cancelled.json()["data"]["status"] == "cancelled"


def test_cross_tenant_visit_returns_404(client: TestClient) -> None:
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
            slug=f"opd-iso-{other.hex[:8]}",
            email=f"opd-iso-{other.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    other_headers = auth_headers(client, tenant["slug"], tenant["email"])
    resp = client.get(f"/api/v1/opd/visits/{visit_id}", headers=other_headers)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_receptionist_cannot_start_consultation(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    resp = client.post(f"/api/v1/opd/visits/{visit_id}/start", json={}, headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_create_walk_in_without_queue(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")

    resp = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
        add_to_queue=False,
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()["data"]
    assert data["token_number"] is None
    assert data["queue_id"] is None


def test_duplicate_patient_doctor_date_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    payload = visit_payload(patient_id=patient_id, doctor_id=str(ctx["doctor_id"]))

    first = client.post("/api/v1/opd/visits", json=payload, headers=headers)
    assert first.status_code == status.HTTP_201_CREATED

    second = client.post("/api/v1/opd/visits", json=payload, headers=headers)
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["errors"][0]["field"] == "patient_id"


def test_update_visit_after_start_returns_409(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])
    patient_id = create_patient(client, headers, phone=f"98765{uuid.uuid4().int % 100000:05d}")
    visit_id = create_visit(
        client,
        headers,
        patient_id=patient_id,
        doctor_id=str(ctx["doctor_id"]),
    ).json()["data"]["id"]

    doctor_email = f"doc-{uuid.uuid4().hex[:8]}@example.com"
    with session_scope() as db:
        from app.core.database import set_rls_tenant_context
        from app.domains.identity.services.rbac_service import RbacProvisioner
        from app.models.core.user import User

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
    started = client.post(f"/api/v1/opd/visits/{visit_id}/start", json={}, headers=doctor_headers)
    assert started.status_code == status.HTTP_200_OK

    updated = client.patch(
        f"/api/v1/opd/visits/{visit_id}",
        json={"chief_complaint": "Too late"},
        headers=headers,
    )
    assert updated.status_code == status.HTTP_409_CONFLICT


def test_create_visit_unknown_patient_returns_404(client: TestClient) -> None:
    ctx = provision_receptionist_with_doctor()
    headers = auth_headers(client, ctx["slug"], ctx["email"])

    resp = client.post(
        "/api/v1/opd/visits",
        json=visit_payload(
            patient_id=str(uuid.uuid4()),
            doctor_id=str(ctx["doctor_id"]),
        ),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["errors"][0]["field"] == "patient_id"


def test_get_visit_detail_includes_latest_vitals(client: TestClient) -> None:
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

    vitals = client.post(
        f"/api/v1/opd/visits/{visit_id}/vitals",
        json={"pulse_rate": 78, "spo2": 98},
        headers=doctor_headers,
    )
    assert vitals.status_code == status.HTTP_201_CREATED, vitals.text

    detail = client.get(f"/api/v1/opd/visits/{visit_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    body = detail.json()["data"]
    assert body["vitals_count"] == 1
    assert body["latest_vitals"] is not None
    assert body["latest_vitals"]["pulse_rate"] == 78
    assert body["latest_vitals"]["spo2"] == 98
