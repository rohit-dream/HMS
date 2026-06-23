"""Integration tests — MVP-038 PermissionResolver Redis cache behavior."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.permissions import PERMISSIONS_CACHE_TTL_SECONDS, PermissionResolver
from app.core.redis_client import get_redis, reset_redis_client
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def redis_client():
    reset_redis_client()
    try:
        client = get_redis()
        client.ping()
    except Exception as exc:
        pytest.skip(f"Redis not available: {exc}")
    yield client
    reset_redis_client()


def _login(client: TestClient, slug: str, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["data"]["access_token"]


def test_permission_cache_stored_with_ttl(
    redis_client, client: TestClient,
) -> None:
    suffix = uuid.uuid4().hex[:8]
    email = f"cache-{suffix}@example.com"
    slug = f"cache-{suffix}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

    token = _login(client, slug, email, "SecurePass@123")
    me = client.get(
        "/api/v1/auth/me",
        headers={TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"},
    )
    assert me.status_code == status.HTTP_200_OK
    assert "opd:queue" in me.json()["data"]["permissions"]

    cache_key = f"tenant:{data['tenant_id']}:permissions:{data['user_id']}"
    ttl = redis_client.ttl(cache_key)
    assert ttl > 0
    assert ttl <= PERMISSIONS_CACHE_TTL_SECONDS


def test_role_assign_invalidates_stale_permission_cache(
    redis_client, client: TestClient,
) -> None:
    suffix = uuid.uuid4().hex[:8]
    admin_email = f"cache-admin-{suffix}@example.com"
    user_email = f"cache-user-{suffix}@example.com"
    slug = f"cache-role-{suffix}"
    password = "SecurePass@123"

    with session_scope() as db:
        admin = provision_tenant_with_role(
            db,
            slug=slug,
            email=admin_email,
            password_hash=hash_password(password),
            role_code="hospital_admin",
        )

    admin_token = _login(client, slug, admin_email, password)
    admin_headers = {
        TENANT_SLUG_HEADER: slug,
        "Authorization": f"Bearer {admin_token}",
    }

    create = client.post(
        "/api/v1/admin/users",
        json={
            "email": user_email,
            "password": password,
            "first_name": "Cache",
            "last_name": "User",
            "role_codes": ["nurse"],
        },
        headers=admin_headers,
    )
    assert create.status_code == status.HTTP_201_CREATED
    user_id = create.json()["data"]["id"]

    user_token = _login(client, slug, user_email, password)
    user_headers = {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {user_token}"}

    me_before = client.get("/api/v1/auth/me", headers=user_headers)
    assert me_before.status_code == status.HTTP_200_OK
    perms_before = set(me_before.json()["data"]["permissions"])
    assert "opd:consult" not in perms_before

    assign = client.post(
        f"/api/v1/admin/users/{user_id}/roles",
        json={"role_code": "doctor"},
        headers=admin_headers,
    )
    assert assign.status_code == status.HTTP_200_OK

    me_after = client.get("/api/v1/auth/me", headers=user_headers)
    assert me_after.status_code == status.HTTP_200_OK
    perms_after = set(me_after.json()["data"]["permissions"])
    assert "opd:consult" in perms_after


def test_invalidate_tenant_clears_permission_keys(redis_client) -> None:
    tenant_id = uuid.uuid4()
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    key_a = f"tenant:{tenant_id}:permissions:{user_a}"
    key_b = f"tenant:{tenant_id}:permissions:{user_b}"
    other_key = f"tenant:{uuid.uuid4()}:permissions:{uuid.uuid4()}"

    redis_client.setex(key_a, PERMISSIONS_CACHE_TTL_SECONDS, "patient:read")
    redis_client.setex(key_b, PERMISSIONS_CACHE_TTL_SECONDS, "billing:read")
    redis_client.setex(other_key, PERMISSIONS_CACHE_TTL_SECONDS, "admin:users")

    with session_scope() as db:
        PermissionResolver(db).invalidate_tenant(tenant_id)

    assert redis_client.get(key_a) is None
    assert redis_client.get(key_b) is None
    assert redis_client.get(other_key) == "admin:users"
