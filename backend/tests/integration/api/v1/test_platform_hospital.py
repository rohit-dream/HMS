"""Multi-tenant platform and hospital management integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def hospital_admin_user():
    tenant_id = uuid.uuid4()
    email = f"hosp-{tenant_id.hex[:8]}@example.com"
    slug = f"hosp-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

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


def test_register_tenant_creates_hospital_resources(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Test Clinic {suffix}",
        "slug": f"test-clinic-{suffix}",
        "email": f"owner-{suffix}@example.com",
        "owner_first_name": "Owner",
        "owner_last_name": "User",
        "owner_password": "SecurePass@123",
    }
    resp = client.post("/api/v1/platform/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()["data"]
    assert body["tenant"]["slug"] == payload["slug"]
    assert body["tenant"]["status"] == "trial"

    headers = {
        TENANT_SLUG_HEADER: payload["slug"],
        "Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': payload['email'], 'password': payload['owner_password']}, headers={TENANT_SLUG_HEADER: payload['slug']}).json()['data']['access_token']}",
    }

    profile = client.get("/api/v1/hospital/profile", headers=headers)
    assert profile.status_code == status.HTTP_200_OK
    assert profile.json()["data"]["name"] == payload["name"]

    locations = client.get("/api/v1/hospital/locations", headers=headers)
    assert locations.status_code == status.HTTP_200_OK
    locs = locations.json()["data"]
    assert len(locs) >= 1
    assert any(loc["code"] == "MAIN" and loc["is_primary"] for loc in locs)

    settings = client.get("/api/v1/hospital/settings", headers=headers)
    assert settings.status_code == status.HTTP_200_OK
    keys = {s["setting_key"] for s in settings.json()["data"]}
    assert "onboarding_progress" in keys
    assert "clinical" in keys


def test_update_hospital_profile(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    resp = client.patch(
        "/api/v1/hospital/profile",
        json={
            "phone": "+91-9876543210",
            "address_line1": "123 Health Street",
            "city": "Mumbai",
            "tax_registration_no": "GSTIN12345",
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["phone"] == "+91-9876543210"
    assert data["city"] == "Mumbai"


def test_create_and_update_location(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/hospital/locations",
        json={"name": "East Wing", "code": "EAST", "city": "Pune"},
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED
    location_id = create.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/hospital/locations/{location_id}",
        json={"phone": "+91-1111111111"},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    assert update.json()["data"]["phone"] == "+91-1111111111"


def test_duplicate_slug_registration_fails(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"dup-{suffix}"
    payload = {
        "name": "Dup Clinic",
        "slug": slug,
        "email": f"dup1-{suffix}@example.com",
        "owner_first_name": "A",
        "owner_last_name": "B",
        "owner_password": "SecurePass@123",
    }
    first = client.post("/api/v1/platform/register", json=payload)
    assert first.status_code == status.HTTP_201_CREATED

    payload["email"] = f"dup2-{suffix}@example.com"
    second = client.post("/api/v1/platform/register", json=payload)
    assert second.status_code == status.HTTP_409_CONFLICT
