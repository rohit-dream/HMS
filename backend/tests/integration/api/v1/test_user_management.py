"""User management integration tests — tenant-scoped admin operations."""

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
def admin_tenant():
    """Tenant with hospital_admin for user management tests."""
    tenant_id = uuid.uuid4()
    email = f"um-admin-{tenant_id.hex[:8]}@example.com"
    slug = f"um-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    yield data


def _auth_headers(slug: str, token: str) -> dict[str, str]:
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _login(client: TestClient, slug: str, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["data"]["access_token"]


def test_create_search_and_get_user(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)

    create_resp = client.post(
        "/api/v1/admin/users",
        json={
            "email": "nurse.new@example.com",
            "password": "NursePass@123",
            "first_name": "Nina",
            "last_name": "Nurse",
            "role_codes": ["nurse"],
        },
        headers=headers,
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    created = create_resp.json()["data"]
    assert created["email"] == "nurse.new@example.com"
    assert created["status"] == "active"
    assert "nurse" in created["roles"]
    user_id = created["id"]

    search_resp = client.get("/api/v1/admin/users?q=nina", headers=headers)
    assert search_resp.status_code == status.HTTP_200_OK
    search_body = search_resp.json()
    assert search_body["meta"]["pagination"]["total_items"] >= 1
    emails = [u["email"] for u in search_body["data"]]
    assert "nurse.new@example.com" in emails

    profile_resp = client.get(f"/api/v1/admin/users/{user_id}", headers=headers)
    assert profile_resp.status_code == status.HTTP_200_OK
    assert profile_resp.json()["data"]["first_name"] == "Nina"


def test_update_user_and_self_profile(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)
    user_id = admin_tenant["user_id"]

    update_resp = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"first_name": "Updated", "phone": "+911234567890"},
        headers=headers,
    )
    assert update_resp.status_code == status.HTTP_200_OK
    assert update_resp.json()["data"]["first_name"] == "Updated"

    self_resp = client.patch(
        "/api/v1/auth/me",
        json={"last_name": "AdminSelf"},
        headers=headers,
    )
    assert self_resp.status_code == status.HTTP_200_OK
    assert self_resp.json()["data"]["last_name"] == "AdminSelf"


def test_invite_user_inactive(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)

    resp = client.post(
        "/api/v1/admin/users/invite",
        json={
            "email": "invited@example.com",
            "first_name": "Inv",
            "last_name": "ited",
            "role_codes": ["receptionist"],
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()["data"]
    assert body["status"] == "inactive"
    assert "receptionist" in body["roles"]


def test_assign_and_remove_role(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)

    create_resp = client.post(
        "/api/v1/admin/users",
        json={
            "email": "role.user@example.com",
            "password": "RolePass@123",
            "first_name": "Role",
            "last_name": "User",
        },
        headers=headers,
    )
    user_id = create_resp.json()["data"]["id"]

    assign_resp = client.post(
        f"/api/v1/admin/users/{user_id}/roles",
        json={"role_code": "doctor"},
        headers=headers,
    )
    assert assign_resp.status_code == status.HTTP_200_OK
    assert "doctor" in assign_resp.json()["data"]["roles"]

    remove_resp = client.delete(
        f"/api/v1/admin/users/{user_id}/roles/doctor",
        headers=headers,
    )
    assert remove_resp.status_code == status.HTTP_200_OK
    assert "doctor" not in remove_resp.json()["data"]["roles"]


def test_cannot_assign_platform_admin(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)
    user_id = admin_tenant["user_id"]

    resp = client.post(
        f"/api/v1/admin/users/{user_id}/roles",
        json={"role_code": "platform_admin"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_disable_user_and_cannot_disable_self(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)

    create_resp = client.post(
        "/api/v1/admin/users",
        json={
            "email": "disable.me@example.com",
            "password": "Disable@123",
            "first_name": "Dis",
            "last_name": "Able",
        },
        headers=headers,
    )
    user_id = create_resp.json()["data"]["id"]

    disable_resp = client.post(f"/api/v1/admin/users/{user_id}/disable", headers=headers)
    assert disable_resp.status_code == status.HTTP_200_OK
    assert disable_resp.json()["data"]["status"] == "inactive"

    self_disable = client.post(
        f"/api/v1/admin/users/{admin_tenant['user_id']}/disable",
        headers=headers,
    )
    assert self_disable.status_code == status.HTTP_403_FORBIDDEN


def test_reset_password_and_token(client: TestClient, admin_tenant: dict) -> None:
    token = _login(client, admin_tenant["slug"], admin_tenant["email"])
    headers = _auth_headers(admin_tenant["slug"], token)

    create_resp = client.post(
        "/api/v1/admin/users",
        json={
            "email": "reset.pw@example.com",
            "password": "OldPass@123",
            "first_name": "Reset",
            "last_name": "User",
        },
        headers=headers,
    )
    user_id = create_resp.json()["data"]["id"]

    reset_resp = client.post(
        f"/api/v1/admin/users/{user_id}/reset-password",
        json={"new_password": "NewPass@456"},
        headers=headers,
    )
    assert reset_resp.status_code == status.HTTP_200_OK
    assert reset_resp.json()["data"]["message"] == "Password reset successfully"

    token_resp = client.post(f"/api/v1/admin/users/{user_id}/reset-token", headers=headers)
    assert token_resp.status_code == status.HTTP_200_OK
    token_body = token_resp.json()["data"]
    assert token_body["reset_token"]
    assert token_body["expires_at"]
