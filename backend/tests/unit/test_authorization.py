"""Unit tests — MVP-039 require_permission dependencies."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.core.authorization import (
    AuthorizationContext,
    RequireAllPermissions,
    RequireAnyPermission,
    RequirePermission,
)
from app.core.exceptions import ForbiddenError
from app.domains.identity.services.auth_service import AuthenticatedUser


def _auth_context(permissions: list[str]) -> AuthorizationContext:
    user = AuthenticatedUser(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        roles=["test_role"],
        jti=uuid.uuid4(),
        token_exp=datetime.now(UTC),
    )
    return AuthorizationContext(user=user, roles=["test_role"], permissions=permissions)


def test_require_permission_allows_granted_permission() -> None:
    dep = RequirePermission("admin:users")
    ctx = _auth_context(["admin:users", "patient:read"])
    assert dep(ctx) is ctx


def test_require_permission_denies_missing_permission() -> None:
    dep = RequirePermission("admin:users")
    ctx = _auth_context(["patient:read"])
    with pytest.raises(ForbiddenError) as exc:
        dep(ctx)
    assert exc.value.field == "permission"
    assert "admin:users" in str(exc.value.message)


def test_require_permission_allows_module_wildcard() -> None:
    dep = RequirePermission("billing:void")
    ctx = _auth_context(["billing:*"])
    assert dep(ctx) is ctx


def test_require_permission_allows_global_wildcard() -> None:
    dep = RequirePermission("admin:settings")
    ctx = _auth_context(["*:*"])
    assert dep(ctx) is ctx


def test_require_any_permission_allows_one_match() -> None:
    dep = RequireAnyPermission("admin:users", "audit:read")
    ctx = _auth_context(["audit:read"])
    assert dep(ctx) is ctx


def test_require_any_permission_denies_when_none_match() -> None:
    dep = RequireAnyPermission("admin:users", "audit:read")
    ctx = _auth_context(["patient:read"])
    with pytest.raises(ForbiddenError):
        dep(ctx)


def test_require_all_permissions_requires_every_permission() -> None:
    dep = RequireAllPermissions("patient:read", "patient:create")
    ctx = _auth_context(["patient:read", "patient:create", "billing:read"])
    assert dep(ctx) is ctx


def test_require_all_permissions_denies_partial_match() -> None:
    dep = RequireAllPermissions("patient:read", "patient:create")
    ctx = _auth_context(["patient:read"])
    with pytest.raises(ForbiddenError):
        dep(ctx)
