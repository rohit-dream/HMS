"""Integration tests — auth events write to audit.audit_logs (MVP-033)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.domains.audit.constants import ACTION_LOGIN, ACTION_LOGOUT, OUTCOME_SUCCESS
from app.models.audit.audit_log import AuditLog
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def _audit_rows(tenant_id: uuid.UUID, *, action: str | None = None) -> list[AuditLog]:
    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_id)
        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        return list(db.scalars(stmt.order_by(AuditLog.created_at)).all())


def test_successful_login_writes_audit_log(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"audit-login-{suffix}@example.com"
    slug = f"audit-login-{suffix}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    headers = {TENANT_SLUG_HEADER: slug}
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    logs = _audit_rows(data["tenant_id"], action=ACTION_LOGIN)
    success_logs = [
        row for row in logs if (row.audit_metadata or {}).get("outcome") == OUTCOME_SUCCESS
    ]
    assert len(success_logs) >= 1
    assert success_logs[-1].user_id is not None
    assert success_logs[-1].entity_type == "user"


def test_failed_login_writes_audit_log(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    email = f"audit-fail-{tenant_id.hex[:8]}@example.com"
    slug = f"audit-fail-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    headers = {TENANT_SLUG_HEADER: slug}
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPass@999"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    logs = _audit_rows(data["tenant_id"], action=ACTION_LOGIN)
    failed = [row for row in logs if (row.audit_metadata or {}).get("outcome") == "failed"]
    assert len(failed) >= 1


def test_logout_writes_audit_log(client: TestClient) -> None:
    tenant_id = uuid.uuid4()
    email = f"audit-logout-{tenant_id.hex[:8]}@example.com"
    slug = f"audit-logout-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

    headers = {TENANT_SLUG_HEADER: slug}
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers=headers,
    )
    assert login.status_code == status.HTTP_200_OK
    token = login.json()["data"]["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={**headers, "Authorization": f"Bearer {token}"},
        cookies=login.cookies,
    )
    assert logout.status_code == status.HTTP_204_NO_CONTENT

    logs = _audit_rows(data["tenant_id"], action=ACTION_LOGOUT)
    assert len(logs) >= 1
    assert logs[-1].user_id == data["user_id"]
