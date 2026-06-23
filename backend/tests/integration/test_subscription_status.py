"""Integration tests — MVP-044 subscription status middleware."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


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


def _login(client: TestClient, slug: str, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["data"]["access_token"]


def _auth_headers(slug: str, token: str) -> dict[str, str]:
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


@pytest.fixture
def trial_tenant():
    suffix = uuid.uuid4().hex[:8]
    slug = f"sub-trial-{suffix}"
    email = f"trial-{suffix}@example.com"
    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
    yield data


def test_trial_tenant_can_mutate_hospital_profile(client: TestClient, trial_tenant: dict) -> None:
    token = _login(client, trial_tenant["slug"], trial_tenant["email"])
    resp = client.patch(
        "/api/v1/hospital/profile",
        json={"phone": "+91-9000000001"},
        headers=_auth_headers(trial_tenant["slug"], token),
    )
    assert resp.status_code == status.HTTP_200_OK


def test_suspended_tenant_blocked_on_authenticated_request(client: TestClient, trial_tenant: dict) -> None:
    token = _login(client, trial_tenant["slug"], trial_tenant["email"])
    _set_tenant_status(trial_tenant["tenant_id"], "suspended")

    resp = client.get("/api/v1/auth/me", headers=_auth_headers(trial_tenant["slug"], token))
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["errors"][0]["code"] == "tenant_suspended"


def test_suspended_tenant_cannot_login(client: TestClient, trial_tenant: dict) -> None:
    _set_tenant_status(trial_tenant["tenant_id"], "suspended")
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": trial_tenant["email"], "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: trial_tenant["slug"]},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_past_due_tenant_read_only_blocks_mutations(client: TestClient, trial_tenant: dict) -> None:
    token = _login(client, trial_tenant["slug"], trial_tenant["email"])
    _set_tenant_status(trial_tenant["tenant_id"], "past_due")

    read_resp = client.get(
        "/api/v1/hospital/profile",
        headers=_auth_headers(trial_tenant["slug"], token),
    )
    assert read_resp.status_code == status.HTTP_200_OK

    write_resp = client.patch(
        "/api/v1/hospital/profile",
        json={"phone": "+91-9000000002"},
        headers=_auth_headers(trial_tenant["slug"], token),
    )
    assert write_resp.status_code == status.HTTP_403_FORBIDDEN
    assert write_resp.json()["errors"][0]["field"] == "subscription"


def test_past_due_tenant_can_logout(client: TestClient, trial_tenant: dict) -> None:
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": trial_tenant["email"], "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: trial_tenant["slug"]},
    )
    token = login_resp.json()["data"]["access_token"]
    _set_tenant_status(trial_tenant["tenant_id"], "past_due")

    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers=_auth_headers(trial_tenant["slug"], token),
        cookies=login_resp.cookies,
    )
    assert logout_resp.status_code == status.HTTP_204_NO_CONTENT
