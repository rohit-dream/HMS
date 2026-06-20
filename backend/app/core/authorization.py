"""
Authorization dependencies and permission decorators.

API protection strategy (RBAC_DESIGN.md §7, §8):
1. Public routes — no auth dependency
2. Authenticated routes — Depends(get_current_user)
3. Protected routes — Depends(require_permission("module:action"))
4. Service layer — explicit checks for resource ownership (future)
5. Repository — tenant_id filter (TenantScopedRepository)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.v1.auth_deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.permissions import PermissionResolver, has_all_permissions, has_any_permission, has_permission
from app.domains.identity.services.auth_service import AuthenticatedUser


@dataclass(frozen=True)
class AuthorizationContext:
    """Authenticated user with resolved roles and permissions."""

    user: AuthenticatedUser
    roles: list[str]
    permissions: list[str]


def get_permission_resolver(db: Session = Depends(get_db)) -> PermissionResolver:
    return PermissionResolver(db)


def get_authorization_context(
    request: Request,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    resolver: PermissionResolver = Depends(get_permission_resolver),
) -> AuthorizationContext:
    """
    Resolve roles and permissions after authentication.

    Sets request.state.permissions for downstream handlers and audit.
    Permissions are server-side resolved (not from JWT) per AUTH guide.
    """
    roles = resolver.get_role_codes(auth_user.tenant_id, auth_user.user_id)
    permissions = resolver.get_permissions(auth_user.tenant_id, auth_user.user_id)

    request.state.permissions = permissions
    request.state.roles = roles

    return AuthorizationContext(user=auth_user, roles=roles, permissions=permissions)


def get_user_permissions(
    ctx: AuthorizationContext = Depends(get_authorization_context),
) -> list[str]:
    """Dependency returning flat permission list."""
    return ctx.permissions


class RequirePermission:
    """FastAPI dependency enforcing a single permission."""

    def __init__(self, permission: str) -> None:
        self.permission = permission

    def __call__(self, ctx: AuthorizationContext = Depends(get_authorization_context)) -> AuthorizationContext:
        if not has_permission(ctx.permissions, self.permission):
            raise ForbiddenError(
                f"Insufficient permissions: requires {self.permission}",
                field="permission",
            )
        return ctx


class RequireAnyPermission:
    """FastAPI dependency requiring at least one of the given permissions."""

    def __init__(self, *permissions: str) -> None:
        self.permissions = permissions

    def __call__(self, ctx: AuthorizationContext = Depends(get_authorization_context)) -> AuthorizationContext:
        if not has_any_permission(ctx.permissions, list(self.permissions)):
            required = ", ".join(self.permissions)
            raise ForbiddenError(
                f"Insufficient permissions: requires one of [{required}]",
                field="permission",
            )
        return ctx


class RequireAllPermissions:
    """FastAPI dependency requiring all listed permissions."""

    def __init__(self, *permissions: str) -> None:
        self.permissions = permissions

    def __call__(self, ctx: AuthorizationContext = Depends(get_authorization_context)) -> AuthorizationContext:
        if not has_all_permissions(ctx.permissions, list(self.permissions)):
            required = ", ".join(self.permissions)
            raise ForbiddenError(
                f"Insufficient permissions: requires all of [{required}]",
                field="permission",
            )
        return ctx


# Convenience aliases for route declarations
require_permission = RequirePermission
require_any_permission = RequireAnyPermission
require_all_permissions = RequireAllPermissions

# Typed shortcuts for common route signatures
AuthorizedUser = Annotated[AuthorizationContext, Depends(get_authorization_context)]
Permitted = RequirePermission
