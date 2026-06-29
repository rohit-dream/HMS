"""Integration tests — mutation audit middleware (MVP-054)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.domains.audit.constants import ACTION_CREATE, ACTION_LOGIN, ACTION_UPDATE
from app.models.audit.audit_log import AuditLog
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


@pytest.fixture
def hospital_admin_user():
    tenant_id = uuid.uuid4()
    email = f"audit-mw-{tenant_id.hex[:8]}@example.com"
    slug = f"audit-mw-{tenant_id.hex[:8]}"

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


def _audit_rows(tenant_id: uuid.UUID, *, action: str | None = None) -> list[AuditLog]:
    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_id)
        stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        return list(db.scalars(stmt.order_by(AuditLog.created_at)).all())


def test_successful_patch_writes_middleware_audit_log(
    client: TestClient,
    hospital_admin_user: dict,
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    before = _audit_rows(hospital_admin_user["tenant_id"])

    resp = client.patch(
        "/api/v1/hospital/profile",
        json={"phone": "+91-9000000001"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK

    after = _audit_rows(hospital_admin_user["tenant_id"])
    middleware_rows = [
        row
        for row in after
        if row not in before
        and (row.audit_metadata or {}).get("source") == "mutation_middleware"
    ]
    assert len(middleware_rows) == 1
    row = middleware_rows[0]
    assert row.action == ACTION_UPDATE
    assert row.entity_type == "profile"
    assert row.user_id == hospital_admin_user["user_id"]
    assert row.new_values == {"phone": "+91-9000000001"}
    assert row.audit_metadata["path"] == "/api/v1/hospital/profile"
    assert row.audit_metadata["http_method"] == "PATCH"


def test_failed_mutation_does_not_write_middleware_audit_log(
    client: TestClient,
    hospital_admin_user: dict,
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    before = _audit_rows(hospital_admin_user["tenant_id"])

    resp = client.patch(
        "/api/v1/hospital/profile",
        json={"currency": "NOT_A_REAL_CURRENCY"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    after = _audit_rows(hospital_admin_user["tenant_id"])
    new_middleware_rows = [
        row
        for row in after
        if row not in before
        and (row.audit_metadata or {}).get("source") == "mutation_middleware"
    ]
    assert new_middleware_rows == []


def test_login_audit_not_duplicated_by_middleware(
    client: TestClient,
    hospital_admin_user: dict,
) -> None:
    before = _audit_rows(hospital_admin_user["tenant_id"], action=ACTION_LOGIN)

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": hospital_admin_user["email"], "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: hospital_admin_user["slug"]},
    )
    assert resp.status_code == status.HTTP_200_OK

    after = _audit_rows(hospital_admin_user["tenant_id"], action=ACTION_LOGIN)
    middleware_login_rows = [
        row
        for row in after
        if row not in before
        and (row.audit_metadata or {}).get("source") == "mutation_middleware"
    ]
    assert middleware_login_rows == []
    assert len(after) == len(before) + 1


def test_post_create_writes_middleware_audit_with_entity_id(
    client: TestClient,
    hospital_admin_user: dict,
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    before = _audit_rows(hospital_admin_user["tenant_id"])

    resp = client.post(
        "/api/v1/hospital/locations",
        json={"name": "Audit Branch", "code": "AUDIT", "city": "Delhi"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    location_id = uuid.UUID(resp.json()["data"]["id"])

    after = _audit_rows(hospital_admin_user["tenant_id"])
    create_rows = [
        row
        for row in after
        if row not in before
        and (row.audit_metadata or {}).get("source") == "mutation_middleware"
    ]
    assert len(create_rows) == 1
    row = create_rows[0]
    assert row.action == ACTION_CREATE
    assert row.entity_type == "locations"
    assert row.entity_id == location_id
    assert row.new_values["code"] == "AUDIT"
