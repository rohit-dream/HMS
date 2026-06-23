"""Unit tests — MVP-038 PermissionResolver Redis caching."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.core.permissions import (
    PERMISSIONS_CACHE_TTL_SECONDS,
    PermissionResolver,
)


@pytest.fixture
def resolver_settings() -> Settings:
    return Settings(
        environment="staging",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
        redis_url="redis://localhost:6379/0",
    )


@pytest.fixture
def tenant_user_ids() -> tuple[uuid.UUID, uuid.UUID]:
    return uuid.uuid4(), uuid.uuid4()


@patch("app.core.permissions.RbacRepository")
@patch("app.core.permissions.get_redis")
def test_get_permissions_uses_redis_cache_hit(
    mock_get_redis: MagicMock,
    mock_repo_cls: MagicMock,
    resolver_settings: Settings,
    tenant_user_ids: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_id, user_id = tenant_user_ids
    redis_client = MagicMock()
    redis_client.get.return_value = "patient:read,billing:create"
    mock_get_redis.return_value = redis_client

    resolver = PermissionResolver(MagicMock(), resolver_settings)
    perms = resolver.get_permissions(tenant_id, user_id)

    assert perms == ["patient:read", "billing:create"]
    mock_repo_cls.return_value.get_user_permissions.assert_not_called()
    redis_client.setex.assert_not_called()


@patch("app.core.permissions.RbacRepository")
@patch("app.core.permissions.get_redis")
def test_get_permissions_populates_cache_on_miss(
    mock_get_redis: MagicMock,
    mock_repo_cls: MagicMock,
    resolver_settings: Settings,
    tenant_user_ids: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_id, user_id = tenant_user_ids
    redis_client = MagicMock()
    redis_client.get.return_value = None
    mock_get_redis.return_value = redis_client
    mock_repo_cls.return_value.get_user_permissions.return_value = {"admin:users", "patient:read"}

    resolver = PermissionResolver(MagicMock(), resolver_settings)
    perms = resolver.get_permissions(tenant_id, user_id)

    assert perms == ["admin:users", "patient:read"]
    cache_key = f"tenant:{tenant_id}:permissions:{user_id}"
    redis_client.setex.assert_called_once_with(
        cache_key,
        PERMISSIONS_CACHE_TTL_SECONDS,
        "admin:users,patient:read",
    )


@patch("app.core.permissions.get_redis")
def test_invalidate_user_deletes_cache_key(
    mock_get_redis: MagicMock,
    resolver_settings: Settings,
    tenant_user_ids: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_id, user_id = tenant_user_ids
    redis_client = MagicMock()
    mock_get_redis.return_value = redis_client

    resolver = PermissionResolver(MagicMock(), resolver_settings)
    resolver.invalidate_user(tenant_id, user_id)

    cache_key = f"tenant:{tenant_id}:permissions:{user_id}"
    redis_client.delete.assert_called_once_with(cache_key)


@patch("app.core.permissions.get_redis")
def test_invalidate_tenant_scans_and_deletes_keys(
    mock_get_redis: MagicMock,
    resolver_settings: Settings,
    tenant_user_ids: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_id, _user_id = tenant_user_ids
    redis_client = MagicMock()
    pattern = f"tenant:{tenant_id}:permissions:*"
    redis_client.scan_iter.return_value = [
        f"tenant:{tenant_id}:permissions:{uuid.uuid4()}",
        f"tenant:{tenant_id}:permissions:{uuid.uuid4()}",
    ]
    mock_get_redis.return_value = redis_client

    resolver = PermissionResolver(MagicMock(), resolver_settings)
    resolver.invalidate_tenant(tenant_id)

    redis_client.scan_iter.assert_called_once_with(match=pattern, count=100)
    assert redis_client.delete.call_count == 2


@patch("app.core.permissions.RbacRepository")
@patch("app.core.permissions.get_redis")
def test_get_permissions_falls_back_to_db_when_redis_unavailable_in_test(
    mock_get_redis: MagicMock,
    mock_repo_cls: MagicMock,
    tenant_user_ids: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_id, user_id = tenant_user_ids
    mock_get_redis.side_effect = ConnectionError("redis down")
    mock_repo_cls.return_value.get_user_permissions.return_value = {"opd:queue"}
    test_settings = Settings(
        environment="test",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
    )

    resolver = PermissionResolver(MagicMock(), test_settings)
    perms = resolver.get_permissions(tenant_id, user_id)

    assert perms == ["opd:queue"]
    mock_repo_cls.return_value.get_user_permissions.assert_called_once_with(tenant_id, user_id)
