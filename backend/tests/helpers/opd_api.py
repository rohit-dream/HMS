"""Shared helpers for OPD visit API integration tests."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.identity.services.rbac_service import RbacProvisioner
from app.models.core.user import User
from tests.helpers.appointments_api import auth_headers, create_patient, provision_receptionist_with_doctor


def provision_doctor_user(ctx: dict) -> str:
    """Create a doctor-role user in the same tenant; returns email."""
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
    return doctor_email


def start_consultation(
    client: TestClient,
    ctx: dict,
    *,
    visit_id: str,
    receptionist_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    """Start visit consultation and return doctor auth headers."""
    doctor_email = provision_doctor_user(ctx)
    doctor_headers = auth_headers(client, ctx["slug"], doctor_email)
    resp = client.post(f"/api/v1/opd/visits/{visit_id}/start", json={}, headers=doctor_headers)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return doctor_headers


def visit_payload(
    *,
    patient_id: str,
    doctor_id: str,
    location_id: str | None = None,
    visit_date: str | None = None,
    **overrides: object,
) -> dict:
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "visit_type": "walk_in",
        "visit_date": visit_date or date.today().isoformat(),
        "chief_complaint": "Fever and cough",
        "add_to_queue": True,
        "queue_priority": "normal",
    }
    if location_id is not None:
        payload["location_id"] = location_id
    payload.update(overrides)
    return payload


def create_visit(
    client: TestClient,
    headers: dict[str, str],
    *,
    patient_id: str,
    doctor_id: str,
    **overrides: object,
):
    return client.post(
        "/api/v1/opd/visits",
        json=visit_payload(patient_id=patient_id, doctor_id=doctor_id, **overrides),
        headers=headers,
    )


def confirm_appointment(client: TestClient, headers: dict[str, str], appointment_id: str) -> None:
    resp = client.post(f"/api/v1/appointments/{appointment_id}/confirm", headers=headers)
    assert resp.status_code == status.HTTP_200_OK, resp.text


__all__ = [
    "auth_headers",
    "confirm_appointment",
    "create_patient",
    "create_visit",
    "provision_doctor_user",
    "provision_receptionist_with_doctor",
    "start_consultation",
    "visit_payload",
]
