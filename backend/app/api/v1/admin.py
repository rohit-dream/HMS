"""
Protected admin endpoints demonstrating RBAC API protection strategy.

Protection layers:
1. Authentication — Depends(get_current_user) via RequirePermission
2. Authorization — require_permission("module:action")
3. Tenant scope — resolved from authenticated user context
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
) -> dict:
    """List tenant users — requires admin:users."""
    return success_response(
        data={"message": "User management endpoint", "roles": ctx.roles},
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/settings")
def get_settings(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
) -> dict:
    """Tenant settings — requires admin:settings."""
    return success_response(
        data={"message": "Tenant settings endpoint"},
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/audit")
def list_audit_logs(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("audit:read")),
) -> dict:
    """Audit log viewer — requires audit:read."""
    return success_response(
        data={"message": "Audit logs endpoint"},
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
