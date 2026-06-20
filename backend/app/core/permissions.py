"""
Permission resolution and authorization checks.

Per AUTHENTICATION_ARCHITECTURE_GUIDE.md (authoritative):
- Permissions are NOT in JWT
- Resolved server-side with Redis cache (TTL 5 min)
- Roles in JWT are UI hints only; DB is source of truth for /me
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.constants import SYSTEM_TENANT_ID
from app.core.redis_client import get_redis
from app.domains.identity.repositories.rbac_repository import RbacRepository

PERMISSIONS_CACHE_PREFIX = "tenant:"
PERMISSIONS_CACHE_SUFFIX = ":permissions:"
PERMISSIONS_CACHE_TTL_SECONDS = 300  # 5 minutes


def has_permission(user_permissions: list[str] | set[str], required: str) -> bool:
    """
    Check if required permission is granted, supporting wildcards.

    Per RBAC_DESIGN.md §7.4:
    - *:* grants all
    - {module}:* grants all actions in module
    """
    perms = set(user_permissions)
    if "*:*" in perms:
        return True
    if required in perms:
        return True
    if ":" in required:
        module, _ = required.split(":", 1)
        if f"{module}:*" in perms:
            return True
    return False


def has_any_permission(user_permissions: list[str] | set[str], required: list[str]) -> bool:
    """Return True if user has at least one of the required permissions."""
    return any(has_permission(user_permissions, perm) for perm in required)


def has_all_permissions(user_permissions: list[str] | set[str], required: list[str]) -> bool:
    """Return True if user has all required permissions."""
    return all(has_permission(user_permissions, perm) for perm in required)


class PermissionResolver:
    """Resolve effective permissions for a user (union of all role permissions)."""

    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self._repo = RbacRepository(db)

    def _cache_key(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> str:
        return f"{PERMISSIONS_CACHE_PREFIX}{tenant_id}{PERMISSIONS_CACHE_SUFFIX}{user_id}"

    def get_role_codes(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> list[str]:
        """Return active role codes assigned to the user."""
        return self._repo.get_user_role_codes(tenant_id, user_id)

    def get_permissions(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> list[str]:
        """Return effective permission codes with Redis caching."""
        cache_key = self._cache_key(tenant_id, user_id)
        try:
            client = get_redis(self.settings)
            cached = client.get(cache_key)
            if cached:
                return cached.split(",") if cached else []
        except Exception:
            if not (self.settings.is_development or self.settings.is_test):
                raise

        permissions = sorted(self._repo.get_user_permissions(tenant_id, user_id))
        try:
            client = get_redis(self.settings)
            client.setex(
                cache_key,
                PERMISSIONS_CACHE_TTL_SECONDS,
                ",".join(permissions),
            )
        except Exception:
            if not (self.settings.is_development or self.settings.is_test):
                raise
        return permissions

    def invalidate_user(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Invalidate permission cache for one user (role assignment change)."""
        try:
            client = get_redis(self.settings)
            client.delete(self._cache_key(tenant_id, user_id))
        except Exception:
            if not (self.settings.is_development or self.settings.is_test):
                raise

    def invalidate_tenant(self, tenant_id: uuid.UUID) -> None:
        """Invalidate all permission caches for a tenant (rare; role template change)."""
        try:
            client = get_redis(self.settings)
            pattern = f"{PERMISSIONS_CACHE_PREFIX}{tenant_id}{PERMISSIONS_CACHE_SUFFIX}*"
            for key in client.scan_iter(match=pattern, count=100):
                client.delete(key)
        except Exception:
            if not (self.settings.is_development or self.settings.is_test):
                raise


def is_system_tenant(tenant_id: uuid.UUID) -> bool:
    return str(tenant_id) == SYSTEM_TENANT_ID
