"""Integration tests — MVP-076 duplicate patient detection API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.patients.repositories.patient_repository import PatientRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"dup-{tenant_id.hex[:8]}@example.com"
    slug = f"dup-{tenant_id.hex[:8]}"

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


def _create_patient(
    client: TestClient,
    headers: dict[str, str],
    *,
    phone: str,
    first_name: str = "Anita",
    last_name: str = "Sharma",
) -> dict:
    resp = client.post(
        "/api/v1/patients",
        json={
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": "1990-01-01",
            "gender": "female",
            "phone": phone,
            **CONSENT_DEFAULTS,
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["data"]


def test_check_duplicate_by_phone(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    created = _create_patient(client, headers, phone="9876530001")

    resp = client.get(
        "/api/v1/patients/check-duplicate",
        params={"phone": "9876530001"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["has_duplicates"] is True
    assert len(data["matches"]) == 1
    assert data["matches"][0]["patient_id"] == created["id"]
    assert "phone" in data["matches"][0]["match_reasons"]


def test_check_duplicate_by_similar_name(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    _create_patient(client, headers, phone="9876530002", first_name="Ravi", last_name="Kumar")

    resp = client.get(
        "/api/v1/patients/check-duplicate",
        params={"first_name": "Ravi", "last_name": "Kumr"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["has_duplicates"] is True
    assert any("name" in m["match_reasons"] for m in data["matches"])


def test_check_duplicate_no_matches(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])

    resp = client.get(
        "/api/v1/patients/check-duplicate",
        params={"phone": "9876530099", "first_name": "Unique"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["has_duplicates"] is False
    assert resp.json()["data"]["matches"] == []


def test_create_blocks_duplicate_phone_without_acknowledgement(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    _create_patient(client, headers, phone="9876530003")

    dup = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Other",
            "date_of_birth": "1991-01-01",
            "gender": "male",
            "phone": "9876530003",
            **CONSENT_DEFAULTS,
        },
        headers=headers,
    )
    assert dup.status_code == status.HTTP_409_CONFLICT


def test_create_allows_duplicate_phone_when_acknowledged(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    _create_patient(client, headers, phone="9876530004")

    dup = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Relative",
            "date_of_birth": "1995-01-01",
            "gender": "male",
            "phone": "9876530004",
            "acknowledge_duplicate": True,
            **CONSENT_DEFAULTS,
        },
        headers=headers,
    )
    assert dup.status_code == status.HTTP_201_CREATED


def test_check_duplicate_cross_tenant_isolation(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"dup-a-{suffix_a}"
    slug_b = f"dup-b-{suffix_b}"
    email_a = f"a-{suffix_a}@example.com"
    email_b = f"b-{suffix_b}@example.com"
    shared_phone = "9876530055"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug_a,
            email=email_a,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        data_b = provision_tenant_with_role(
            db,
            slug=slug_b,
            email=email_b,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        set_rls_tenant_context(db, data_b["tenant_id"])
        PatientRepository(db, data_b["tenant_id"]).create(
            mrn="MRN-DUP-00001",
            first_name="Hidden",
            date_of_birth=date(1990, 1, 1),
            gender="male",
            phone=shared_phone,
        )
        db.commit()

    headers_a = _auth_headers(client, slug_a, email_a)
    resp = client.get(
        "/api/v1/patients/check-duplicate",
        params={"phone": shared_phone},
        headers=headers_a,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["has_duplicates"] is False


def test_check_duplicate_requires_patient_create_permission(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"dup-pharm-{suffix}"
    email = f"pharm-{suffix}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="pharmacist",
        )

    headers = _auth_headers(client, slug, email)
    resp = client.get(
        "/api/v1/patients/check-duplicate",
        params={"phone": "9876530066"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
