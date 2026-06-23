"""MVP-032 — API end-to-end auth workflow tests."""

from __future__ import annotations

import logging
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from sqlalchemy import select

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.models.core.user import User
from app.domains.identity.constants import (
    EMAIL_VERIFICATION_SUCCESS_MESSAGE,
    FORGOT_PASSWORD_MESSAGE,
    RESET_PASSWORD_SUCCESS_MESSAGE,
)
from tests.helpers.auth import register_payload, token_from_caplog
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def test_e2e_register_login_me_logout(client: TestClient) -> None:
    """Smoke: self-service register → login → /me → logout."""
    payload = register_payload()
    register = client.post("/api/v1/platform/register", json=payload)
    assert register.status_code == status.HTTP_201_CREATED

    headers = {TENANT_SLUG_HEADER: payload["slug"]}
    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["owner_password"]},
        headers=headers,
    )
    assert login.status_code == status.HTTP_200_OK
    access_token = login.json()["data"]["access_token"]
    auth_headers = {**headers, "Authorization": f"Bearer {access_token}"}

    me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == status.HTTP_200_OK
    assert me.json()["data"]["email"] == payload["email"]
    assert "hospital_owner" in me.json()["data"]["roles"]

    refresh = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
        cookies=login.cookies,
    )
    assert refresh.status_code == status.HTTP_200_OK
    new_token = refresh.json()["data"]["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={**headers, "Authorization": f"Bearer {new_token}"},
        cookies=refresh.cookies,
    )
    assert logout.status_code == status.HTTP_204_NO_CONTENT

    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
        cookies=refresh.cookies,
    )
    assert refresh_after_logout.status_code == status.HTTP_401_UNAUTHORIZED


def test_e2e_forgot_reset_login(client: TestClient, caplog) -> None:
    """Smoke: forgot-password → reset-password → login with new password."""
    suffix = uuid.uuid4().hex[:8]
    email = f"e2e-reset-{suffix}@example.com"
    slug = f"e2e-reset-{suffix}"
    old_password = "SecurePass@123"
    new_password = "NewSecurePass@456"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password(old_password),
            role_code="hospital_admin",
        )

    headers = {TENANT_SLUG_HEADER: slug}
    with caplog.at_level(logging.INFO):
        forgot = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
            headers=headers,
        )
    assert forgot.status_code == status.HTTP_200_OK
    assert forgot.json()["data"]["message"] == FORGOT_PASSWORD_MESSAGE

    token = token_from_caplog(caplog, "password_reset_token_issued", email)
    assert token is not None

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": new_password},
    )
    assert reset.status_code == status.HTTP_200_OK
    assert reset.json()["data"]["message"] == RESET_PASSWORD_SUCCESS_MESSAGE

    login_old = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
        headers=headers,
    )
    assert login_old.status_code == status.HTTP_401_UNAUTHORIZED

    login_new = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
        headers=headers,
    )
    assert login_new.status_code == status.HTTP_200_OK
    assert login_new.json()["data"]["access_token"]


def test_e2e_verify_email_after_resend(client: TestClient, caplog) -> None:
    """Smoke: login → resend verification → verify email from dev token log."""
    suffix = uuid.uuid4().hex[:8]
    email = f"e2e-verify-{suffix}@example.com"
    slug = f"e2e-verify-{suffix}"
    password = "SecurePass@123"

    with session_scope() as db:
        tenant_user = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password(password),
            role_code="hospital_admin",
        )

    headers = {TENANT_SLUG_HEADER: slug}
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers=headers,
    )
    assert login.status_code == status.HTTP_200_OK
    auth_headers = {
        **headers,
        "Authorization": f"Bearer {login.json()['data']['access_token']}",
    }

    with caplog.at_level(logging.INFO):
        resend = client.post(
            "/api/v1/auth/resend-verification",
            headers=auth_headers,
        )
    assert resend.status_code == status.HTTP_200_OK

    token = token_from_caplog(caplog, "email_verification_token_issued", email)
    assert token is not None

    verify = client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert verify.status_code == status.HTTP_200_OK
    assert verify.json()["data"]["message"] == EMAIL_VERIFICATION_SUCCESS_MESSAGE

    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_user["tenant_id"])
        user = db.scalars(select(User).where(User.id == tenant_user["user_id"])).first()
        assert user is not None
        assert user.email_verified_at is not None


def test_login_lockout_after_five_failures(client: TestClient) -> None:
    """Account locks after LOCKOUT_THRESHOLD failed login attempts."""
    suffix = uuid.uuid4().hex[:8]
    email = f"e2e-lockout-{suffix}@example.com"
    slug = f"e2e-lockout-{suffix}"
    password = "SecurePass@123"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password(password),
            role_code="hospital_admin",
        )

    headers = {TENANT_SLUG_HEADER: slug}
    for attempt in range(4):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword@999"},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED, f"attempt {attempt + 1}"

    locked = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword@999"},
        headers=headers,
    )
    assert locked.status_code == status.HTTP_423_LOCKED

    correct_while_locked = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers=headers,
    )
    assert correct_while_locked.status_code == status.HTTP_423_LOCKED


def test_same_email_different_tenants_independent_login(client: TestClient) -> None:
    """Same email in two tenants logs into the tenant resolved by X-Tenant-Slug."""
    suffix = uuid.uuid4().hex[:8]
    shared_email = f"shared-{suffix}@example.com"
    password = "SecurePass@123"
    slug_a = f"e2e-shared-a-{suffix}"
    slug_b = f"e2e-shared-b-{suffix}"

    with session_scope() as db:
        tenant_a = provision_tenant_with_role(
            db,
            slug=slug_a,
            email=shared_email,
            password_hash=hash_password(password),
            role_code="hospital_admin",
        )
        tenant_b = provision_tenant_with_role(
            db,
            slug=slug_b,
            email=shared_email,
            password_hash=hash_password(password),
            role_code="hospital_admin",
        )

    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": shared_email, "password": password},
        headers={TENANT_SLUG_HEADER: slug_a},
    )
    assert login_a.status_code == status.HTTP_200_OK
    me_a = client.get(
        "/api/v1/auth/me",
        headers={
            TENANT_SLUG_HEADER: slug_a,
            "Authorization": f"Bearer {login_a.json()['data']['access_token']}",
        },
    )
    assert me_a.status_code == status.HTTP_200_OK
    assert me_a.json()["data"]["tenant_id"] == str(tenant_a["tenant_id"])

    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": shared_email, "password": password},
        headers={TENANT_SLUG_HEADER: slug_b},
    )
    assert login_b.status_code == status.HTTP_200_OK
    me_b = client.get(
        "/api/v1/auth/me",
        headers={
            TENANT_SLUG_HEADER: slug_b,
            "Authorization": f"Bearer {login_b.json()['data']['access_token']}",
        },
    )
    assert me_b.status_code == status.HTTP_200_OK
    assert me_b.json()["data"]["tenant_id"] == str(tenant_b["tenant_id"])
    assert me_a.json()["data"]["tenant_id"] != me_b.json()["data"]["tenant_id"]

    wrong_slug = client.post(
        "/api/v1/auth/login",
        json={"email": shared_email, "password": password},
        headers={TENANT_SLUG_HEADER: f"nonexistent-{suffix}"},
    )
    assert wrong_slug.status_code == status.HTTP_404_NOT_FOUND
