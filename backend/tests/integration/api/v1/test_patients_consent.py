"""Integration tests — MVP-077 patient consent on registration (FR-PAT-009)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"consent-{tenant_id.hex[:8]}@example.com"
    slug = f"consent-{tenant_id.hex[:8]}"

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


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _base_payload(**overrides: object) -> dict:
    payload = {
        "first_name": "Priya",
        "last_name": "Nair",
        "date_of_birth": "1992-06-10",
        "gender": "female",
        "phone": "9876012345",
        **CONSENT_DEFAULTS,
    }
    payload.update(overrides)
    return payload


def test_create_patient_records_consent_timestamp_and_method(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    before = datetime.now(UTC)

    resp = client.post(
        "/api/v1/patients",
        json=_base_payload(consent_method="written"),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()["data"]
    assert data["consent_method"] == "written"
    assert data["consent_given_at"] is not None

    given_at = datetime.fromisoformat(data["consent_given_at"].replace("Z", "+00:00"))
    assert given_at >= before
    assert given_at <= datetime.now(UTC)


@pytest.mark.parametrize("method", ["written", "verbal", "digital"])
def test_create_patient_accepts_valid_consent_methods(
    client: TestClient, receptionist_user: dict, method: str
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    phone = f"98765{uuid.uuid4().int % 100000:05d}"

    resp = client.post(
        "/api/v1/patients",
        json=_base_payload(phone=phone, consent_method=method),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["data"]["consent_method"] == method


def test_create_patient_rejects_missing_consent_fields(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    payload = _base_payload()
    del payload["data_processing_consent"]
    del payload["consent_method"]

    resp = client.post("/api/v1/patients", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_patient_rejects_false_consent_flag(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])

    resp = client.post(
        "/api/v1/patients",
        json=_base_payload(data_processing_consent=False),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_patient_rejects_invalid_consent_method(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])

    resp = client.post(
        "/api/v1/patients",
        json=_base_payload(consent_method="email"),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
