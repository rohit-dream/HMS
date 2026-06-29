"""Integration tests — MVP-078 trial patient cap (402)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.patients.repositories.patient_repository import PatientRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"cap-{tenant_id.hex[:8]}@example.com"
    slug = f"cap-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    yield data


@pytest.fixture
def low_trial_patient_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.tenant.limits.TRIAL_PATIENT_LIMIT", 2)


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _patient_payload(*, phone: str) -> dict:
    return {
        "first_name": "Cap",
        "last_name": "Patient",
        "date_of_birth": "1990-01-01",
        "gender": "female",
        "phone": phone,
        **CONSENT_DEFAULTS,
    }


def _set_tenant_status(tenant_id: uuid.UUID, status_value: str) -> None:
    with session_scope() as db:
        db.execute(text("RESET ROLE"))
        db.execute(
            text(
                """
                UPDATE platform.tenants
                SET status = :status, updated_at = NOW()
                WHERE id = :tenant_id
                """
            ),
            {"status": status_value, "tenant_id": tenant_id},
        )
        db.commit()


def test_trial_patient_cap_returns_402_when_exceeded(
    client: TestClient,
    receptionist_user: dict,
    low_trial_patient_cap: None,
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])

    assert (
        client.post(
            "/api/v1/patients",
            json=_patient_payload(phone="9876010001"),
            headers=headers,
        ).status_code
        == status.HTTP_201_CREATED
    )
    assert (
        client.post(
            "/api/v1/patients",
            json=_patient_payload(phone="9876010002"),
            headers=headers,
        ).status_code
        == status.HTTP_201_CREATED
    )

    blocked = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9876010003"),
        headers=headers,
    )
    assert blocked.status_code == status.HTTP_402_PAYMENT_REQUIRED
    error = blocked.json()["errors"][0]
    assert error["code"] == "plan_limit_patients"
    assert error["field"] == "patients"


def test_active_tenant_bypasses_trial_patient_cap(
    client: TestClient,
    receptionist_user: dict,
    low_trial_patient_cap: None,
) -> None:
    _set_tenant_status(receptionist_user["tenant_id"], "active")
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])

    for suffix in ("1", "2", "3"):
        resp = client.post(
            "/api/v1/patients",
            json=_patient_payload(phone=f"987602000{suffix}"),
            headers=headers,
        )
        assert resp.status_code == status.HTTP_201_CREATED


def test_soft_deleted_patients_do_not_count_toward_cap(
    client: TestClient,
    receptionist_user: dict,
    low_trial_patient_cap: None,
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])

    first = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9876030001"),
        headers=headers,
    )
    second = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9876030002"),
        headers=headers,
    )
    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_201_CREATED
    patient_id = uuid.UUID(first.json()["data"]["id"])

    with session_scope() as db:
        set_rls_tenant_context(db, receptionist_user["tenant_id"])
        patient = PatientRepository(db, receptionist_user["tenant_id"]).get_by_id(patient_id)
        assert patient is not None
        PatientRepository(db, receptionist_user["tenant_id"]).soft_delete(patient)
        db.commit()

    replacement = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9876030003"),
        headers=headers,
    )
    assert replacement.status_code == status.HTTP_201_CREATED
