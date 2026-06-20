"""RBAC integration tests — protected endpoints and permission enforcement."""

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
def rbac_tenant_user():
    """Tenant with hospital_admin role and full RBAC provisioned."""
    tenant_id = uuid.uuid4()
    email = f"rbac-{tenant_id.hex[:8]}@example.com"
    slug = f"rbac-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    yield data


@pytest.fixture
def receptionist_user():
    """Tenant with receptionist role (no admin:users)."""
    tenant_id = uuid.uuid4()
    email = f"recv-{tenant_id.hex[:8]}@example.com"
    slug = f"recv-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

    yield data


def _login(client: TestClient, slug: str, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["data"]["access_token"]


def test_hospital_admin_can_access_admin_users(client: TestClient, rbac_tenant_user: dict) -> None:
    token = _login(client, rbac_tenant_user["slug"], rbac_tenant_user["email"])
    resp = client.get(
        "/api/v1/admin/users",
        headers={
            TENANT_SLUG_HEADER: rbac_tenant_user["slug"],
            "Authorization": f"Bearer {token}",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["message"] == "User management endpoint"


def test_receptionist_denied_admin_users(client: TestClient, receptionist_user: dict) -> None:
    token = _login(client, receptionist_user["slug"], receptionist_user["email"])
    resp = client.get(
        "/api/v1/admin/users",
        headers={
            TENANT_SLUG_HEADER: receptionist_user["slug"],
            "Authorization": f"Bearer {token}",
        },
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["errors"][0]["code"] == "forbidden"


def test_receptionist_can_read_patients(client: TestClient, receptionist_user: dict) -> None:
    token = _login(client, receptionist_user["slug"], receptionist_user["email"])
    resp = client.get(
        "/api/v1/patients",
        headers={
            TENANT_SLUG_HEADER: receptionist_user["slug"],
            "Authorization": f"Bearer {token}",
        },
    )
    assert resp.status_code == status.HTTP_200_OK


def test_me_returns_resolved_permissions(client: TestClient, rbac_tenant_user: dict) -> None:
    token = _login(client, rbac_tenant_user["slug"], rbac_tenant_user["email"])
    resp = client.get(
        "/api/v1/auth/me",
        headers={
            TENANT_SLUG_HEADER: rbac_tenant_user["slug"],
            "Authorization": f"Bearer {token}",
        },
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()["data"]
    assert "hospital_admin" in body["roles"]
    assert "admin:users" in body["permissions"]
    assert "patient:read" in body["permissions"]
