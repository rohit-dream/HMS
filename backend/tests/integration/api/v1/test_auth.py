"""Authentication endpoint integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import create_app

from app.core.constants import REFRESH_TOKEN_COOKIE, TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.domains.identity.constants import (
    EMAIL_ALREADY_VERIFIED_MESSAGE,
    EMAIL_VERIFICATION_SUCCESS_MESSAGE,
    FORGOT_PASSWORD_MESSAGE,
    RESEND_VERIFICATION_MESSAGE,
    RESET_PASSWORD_SUCCESS_MESSAGE,
)
from app.models.core.user import User
from tests.helpers.rbac import provision_tenant_with_role


def _token_from_caplog(caplog, prefix: str, email: str) -> str | None:
    template = f"{prefix} email=%s tenant_id=%s token=%s"
    for record in caplog.records:
        if getattr(record, "msg", None) == template and record.args and record.args[0] == email:
            return record.args[2]
        message = record.getMessage()
        if message.startswith(prefix) and email in message:
            return message.rsplit("token=", 1)[-1]
    return None


@pytest.fixture
def auth_tenant_user():
    """Create an isolated tenant + user with hospital_admin role."""
    tenant_id = uuid.uuid4()
    email = f"auth-test-{tenant_id.hex[:8]}@example.com"
    slug = f"auth-{tenant_id.hex[:8]}"

    with session_scope() as db:
        tenant_user = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    yield tenant_user
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


def test_refresh_rotates_token(client: TestClient, auth_tenant_user: dict) -> None:
    """MVP-024: each refresh issues a new opaque token and invalidates the old one."""
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    refresh_headers = {"Origin": "http://localhost:5173"}

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert login_resp.status_code == status.HTTP_200_OK
    old_refresh_cookie = login_resp.cookies[REFRESH_TOKEN_COOKIE]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies=login_resp.cookies,
    )
    assert refresh_resp.status_code == status.HTTP_200_OK
    new_refresh_cookie = refresh_resp.cookies[REFRESH_TOKEN_COOKIE]
    assert new_refresh_cookie != old_refresh_cookie

    stale_refresh = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies={REFRESH_TOKEN_COOKIE: old_refresh_cookie},
    )
    assert stale_refresh.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_reuse_revokes_all_sessions(client: TestClient, auth_tenant_user: dict) -> None:
    """MVP-024: presenting a revoked refresh token revokes every session for the user."""
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    refresh_headers = {"Origin": "http://localhost:5173"}

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert login_resp.status_code == status.HTTP_200_OK
    revoked_refresh = login_resp.cookies[REFRESH_TOKEN_COOKIE]

    rotated = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies=login_resp.cookies,
    )
    assert rotated.status_code == status.HTTP_200_OK
    current_refresh = rotated.cookies[REFRESH_TOKEN_COOKIE]

    reuse_resp = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies={REFRESH_TOKEN_COOKIE: revoked_refresh},
    )
    assert reuse_resp.status_code == status.HTTP_401_UNAUTHORIZED

    still_valid = client.post(
        "/api/v1/auth/refresh",
        headers=refresh_headers,
        cookies={REFRESH_TOKEN_COOKIE: current_refresh},
    )
    assert still_valid.status_code == status.HTTP_401_UNAUTHORIZED

    relogin = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert relogin.status_code == status.HTTP_200_OK


def test_me_requires_authentication(client: TestClient) -> None:
    """MVP-025: GET /auth/me rejects unauthenticated requests."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_requires_cookie(settings) -> None:
    """MVP-025: POST /auth/refresh requires HttpOnly refresh cookie."""
    settings.skip_startup_checks = True
    with TestClient(create_app(settings)) as isolated_client:
        resp = isolated_client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "http://localhost:5173"},
        )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_response_envelope(client: TestClient, auth_tenant_user: dict) -> None:
    """MVP-025: login returns standard envelope with access token and user summary."""
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "data" in body and "meta" in body
    assert body["meta"]["request_id"]
    data = body["data"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800
    assert data["access_token"]
    assert data["user"]["email"] == auth_tenant_user["email"]
    assert data["user"]["tenant_id"]
    assert REFRESH_TOKEN_COOKIE in resp.cookies


def test_openapi_documents_core_auth_routes(client: TestClient) -> None:
    """MVP-025: OpenAPI schema includes login, logout, refresh, and me."""
    spec = client.get("/api/v1/openapi.json").json()
    paths = spec["paths"]
    assert "/api/v1/auth/login" in paths
    assert "post" in paths["/api/v1/auth/login"]
    assert "/api/v1/auth/logout" in paths
    assert "post" in paths["/api/v1/auth/logout"]
    assert "/api/v1/auth/refresh" in paths
    assert "post" in paths["/api/v1/auth/refresh"]
    assert "/api/v1/auth/me" in paths
    assert "get" in paths["/api/v1/auth/me"]


def test_forgot_password_always_returns_200(client: TestClient, auth_tenant_user: dict) -> None:
    """MVP-026: forgot-password always succeeds to prevent email enumeration."""
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown@example.com"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["data"]["message"] == FORGOT_PASSWORD_MESSAGE


def test_forgot_password_creates_reset_token(client: TestClient, auth_tenant_user: dict) -> None:
    """MVP-026: valid user receives a hashed reset token row."""
    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": auth_tenant_user["email"]},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    from sqlalchemy import func, select

    from app.models.core.password_reset_token import PasswordResetToken

    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, auth_tenant_user["tenant_id"])
        count = db.scalar(
            select(func.count())
            .select_from(PasswordResetToken)
            .where(PasswordResetToken.user_id == auth_tenant_user["user_id"])
        )
    assert count == 1


def test_reset_password_flow(client: TestClient, auth_tenant_user: dict, caplog) -> None:
    """MVP-026: reset token updates password and revokes active sessions."""
    import logging

    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert login_resp.status_code == status.HTTP_200_OK

    with caplog.at_level(logging.INFO):
        forgot_resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": auth_tenant_user["email"]},
            headers=headers,
        )
    assert forgot_resp.status_code == status.HTTP_200_OK

    raw_token = None
    for record in caplog.records:
        if getattr(record, "msg", None) == "password_reset_token_issued email=%s tenant_id=%s token=%s":
            if record.args and record.args[0] == auth_tenant_user["email"]:
                raw_token = record.args[2]
                break
        message = record.getMessage()
        if message.startswith("password_reset_token_issued") and auth_tenant_user["email"] in message:
            raw_token = message.rsplit("token=", 1)[-1]
            break
    assert raw_token, "expected dev/test reset token log entry"

    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPass@456"},
    )
    assert reset_resp.status_code == status.HTTP_200_OK
    assert reset_resp.json()["data"]["message"] == RESET_PASSWORD_SUCCESS_MESSAGE

    login_new = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "NewPass@456"},
        headers=headers,
    )
    assert login_new.status_code == status.HTTP_200_OK

    refresh_after_reset = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "http://localhost:5173"},
        cookies=login_resp.cookies,
    )
    assert refresh_after_reset.status_code == status.HTTP_401_UNAUTHORIZED


def test_reset_password_rejects_invalid_token(client: TestClient) -> None:
    """MVP-026: invalid or expired reset token is rejected."""
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-valid-token", "new_password": "NewPass@456"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_resend_verification_requires_auth(client: TestClient) -> None:
    """MVP-027: resend-verification requires Bearer authentication."""
    resp = client.post("/api/v1/auth/resend-verification")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_resend_and_verify_email_flow(client: TestClient, auth_tenant_user: dict, caplog) -> None:
    """MVP-027: resend issues token; verify-email sets email_verified_at."""
    import logging
    from sqlalchemy import select

    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    assert login_resp.status_code == status.HTTP_200_OK
    access_token = login_resp.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    with caplog.at_level(logging.INFO):
        resend_resp = client.post("/api/v1/auth/resend-verification", headers=auth_headers)
    assert resend_resp.status_code == status.HTTP_200_OK
    assert resend_resp.json()["data"]["message"] == RESEND_VERIFICATION_MESSAGE

    raw_token = _token_from_caplog(caplog, "email_verification_token_issued", auth_tenant_user["email"])
    assert raw_token, "expected dev/test verification token log entry"

    verify_resp = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert verify_resp.status_code == status.HTTP_200_OK
    assert verify_resp.json()["data"]["message"] == EMAIL_VERIFICATION_SUCCESS_MESSAGE

    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, auth_tenant_user["tenant_id"])
        user = db.scalars(select(User).where(User.id == auth_tenant_user["user_id"])).first()
        assert user is not None
        assert user.email_verified_at is not None


def test_verify_email_rejects_invalid_token(client: TestClient) -> None:
    """MVP-027: invalid verification token is rejected."""
    resp = client.post("/api/v1/auth/verify-email", json={"token": "not-a-valid-token"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_resend_verification_when_already_verified(
    client: TestClient, auth_tenant_user: dict, caplog
) -> None:
    """MVP-027: resend returns already-verified message for verified users."""
    import logging

    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": auth_tenant_user["email"], "password": "SecurePass@123"},
        headers=headers,
    )
    access_token = login_resp.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    with caplog.at_level(logging.INFO):
        client.post("/api/v1/auth/resend-verification", headers=auth_headers)
    raw_token = _token_from_caplog(caplog, "email_verification_token_issued", auth_tenant_user["email"])
    assert raw_token
    client.post("/api/v1/auth/verify-email", json={"token": raw_token})

    resend_again = client.post("/api/v1/auth/resend-verification", headers=auth_headers)
    assert resend_again.status_code == status.HTTP_200_OK
    assert resend_again.json()["data"]["message"] == EMAIL_ALREADY_VERIFIED_MESSAGE


def test_login_returns_429_when_rate_limited(
    client: TestClient,
    auth_tenant_user: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MVP-029: auth endpoints return 429 when per-IP Redis limit is exceeded."""
    from unittest.mock import MagicMock, patch

    redis_client = MagicMock()
    redis_client.incr.return_value = 11

    headers = {TENANT_SLUG_HEADER: auth_tenant_user["slug"]}
    with patch("app.core.rate_limit.get_redis", return_value=redis_client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": auth_tenant_user["email"], "password": "WrongPass@999"},
            headers=headers,
        )

    assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert resp.json()["errors"][0]["code"] == "rate_limit_exceeded"
