"""MVP-041 — accept-invite API and invite token flow."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password, hash_refresh_token
from app.domains.identity.repositories.user_invite_repository import UserInviteRepository
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def _auth_headers(slug: str, token: str) -> dict[str, str]:
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _login(client: TestClient, slug: str, email: str, password: str = "SecurePass@123") -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["data"]["access_token"]


def test_accept_invite_activates_user_and_issues_tokens(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"invite-{suffix}"
    admin_email = f"admin-{suffix}@example.com"
    invited_email = f"invited-{suffix}@example.com"
    new_password = "InvitePass@123"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=admin_email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    admin_token = _login(client, slug, admin_email)
    admin_headers = _auth_headers(slug, admin_token)

    invite_resp = client.post(
        "/api/v1/admin/users/invite",
        json={
            "email": invited_email,
            "first_name": "Inv",
            "last_name": "ited",
            "role_codes": ["receptionist"],
        },
        headers=admin_headers,
    )
    assert invite_resp.status_code == status.HTTP_201_CREATED
    invite_body = invite_resp.json()["data"]
    invite_token = invite_body["invite_token"]
    assert invite_body["status"] == "inactive"

    accept_resp = client.post(
        "/api/v1/auth/accept-invite",
        json={"invite_token": invite_token, "password": new_password},
    )
    assert accept_resp.status_code == status.HTTP_200_OK
    accept_data = accept_resp.json()["data"]
    assert accept_data["access_token"]
    assert accept_data["user"]["email"] == invited_email
    assert "receptionist" in accept_data["user"]["roles"]

    me_headers = _auth_headers(slug, accept_data["access_token"])
    me_resp = client.get("/api/v1/auth/me", headers=me_headers)
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.json()["data"]["email"] == invited_email

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": invited_email, "password": new_password},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert login_resp.status_code == status.HTTP_200_OK


def test_accept_invite_invalid_token(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/auth/accept-invite",
        json={"invite_token": "not-a-valid-token", "password": "SecurePass@123"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_accept_invite_token_single_use(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"invite-once-{suffix}"
    admin_email = f"admin-once-{suffix}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=admin_email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    admin_token = _login(client, slug, admin_email)
    invite_resp = client.post(
        "/api/v1/admin/users/invite",
        json={
            "email": f"once-{suffix}@example.com",
            "first_name": "Once",
            "last_name": "User",
            "role_codes": ["nurse"],
        },
        headers=_auth_headers(slug, admin_token),
    )
    invite_token = invite_resp.json()["data"]["invite_token"]
    payload = {"invite_token": invite_token, "password": "OncePass@123"}

    first = client.post("/api/v1/auth/accept-invite", json=payload)
    assert first.status_code == status.HTTP_200_OK

    second = client.post("/api/v1/auth/accept-invite", json=payload)
    assert second.status_code == status.HTTP_401_UNAUTHORIZED


def test_invite_sends_accept_invite_email(client: TestClient, caplog) -> None:
    """MVP-043: invite flow logs email with accept-invite URL."""
    import logging

    suffix = uuid.uuid4().hex[:8]
    slug = f"invite-email-{suffix}"
    admin_email = f"admin-email-{suffix}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=admin_email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    admin_token = _login(client, slug, admin_email)
    with caplog.at_level(logging.INFO):
        invite_resp = client.post(
            "/api/v1/admin/users/invite",
            json={
                "email": f"staff-{suffix}@example.com",
                "first_name": "Staff",
                "last_name": "User",
                "role_codes": ["nurse"],
            },
            headers=_auth_headers(slug, admin_token),
        )
    assert invite_resp.status_code == status.HTTP_201_CREATED

    messages = [r.getMessage() for r in caplog.records]
    assert any("email_sent template=user_invite" in m for m in messages)
    assert any("/accept-invite?" in m for m in messages)
    assert any("user_invite_token_issued" in m for m in messages)


def test_accept_invite_expired_token(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"invite-exp-{suffix}"
    email = f"exp-{suffix}@example.com"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        repo = UserInviteRepository(db, data["tenant_id"])
        raw_token = "expired-invite-token-value"
        repo.create_token(
            user_id=data["user_id"],
            token_hash=hash_refresh_token(raw_token),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            created_by=data["user_id"],
        )
        db.commit()

    resp = client.post(
        "/api/v1/auth/accept-invite",
        json={"invite_token": raw_token, "password": "SecurePass@123"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
