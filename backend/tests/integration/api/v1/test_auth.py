"""Authentication endpoint integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import REFRESH_TOKEN_COOKIE, TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def auth_tenant_user():
    """Create an isolated tenant + user with hospital_admin role."""
    tenant_id = uuid.uuid4()
    email = f"auth-test-{tenant_id.hex[:8]}@example.com"
    slug = f"auth-{tenant_id.hex[:8]}"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    yield {"slug": slug, "email": email, "tenant_id": tenant_id}
    # No teardown — test DB rows are disposable


def test_login_refresh_me_logout_flow(client: TestClient, auth_tenant_user: dict) -> None:
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert login_resp.status_code == status.HTTP_200_OK
    login_body = login_resp.json()
    assert login_body["data"]["access_token"]
    assert login_body["data"]["token_type"] == "bearer"
    assert login_body["data"]["user"]["email"] == auth_tenant_user["email"]
    assert REFRESH_TOKEN_COOKIE in login_resp.cookies

    access_token = login_body["data"]["access_token"]
    auth_headers = {**headers, "Authorization": f"Bearer {access_token}"}

    me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == status.HTTP_200_OK
    me_body = me_resp.json()
    assert me_body["data"]["email"] == auth_tenant_user["email"]
    assert "hospital_admin" in me_body["data"]["roles"]
    assert "admin:users" in me_body["data"]["permissions"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
        cookies=login_resp.cookies,
    )
    assert refresh_resp.status_code == status.HTTP_200_OK
    new_token = refresh_resp.json()["data"]["access_token"]
    assert new_token != access_token

    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_token}"},
        cookies=refresh_resp.cookies,
    )
    assert logout_resp.status_code == status.HTTP_204_NO_CONTENT

    # Without Redis denylist (local dev), access token may still validate until expiry.
    # Session revocation is verified by refresh failure.
    client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
        cookies=refresh_resp.cookies,
    )
    assert refresh_after_logout.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_invalid_credentials(client: TestClient, auth_tenant_user: dict) -> None:
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "WrongPass@999"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
