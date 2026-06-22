"""Admin endpoints — settings, audit (user routes in admin_users)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings")
def get_settings(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
) -> dict:
    """Tenant settings placeholder — see /hospital/settings for full implementation."""
    return success_response(
        data={"message": "Use GET /api/v1/hospital/settings for tenant configuration"},
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
