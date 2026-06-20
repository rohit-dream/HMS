"""Patient endpoints — protected by clinical RBAC permissions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
) -> dict:
    """List patients — requires patient:read."""
    return success_response(
        data={"message": "Patient list endpoint", "permission": "patient:read"},
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("")
def create_patient(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("patient:create")),
) -> dict:
    """Register patient — requires patient:create."""
    return success_response(
        data={"message": "Patient registration endpoint", "permission": "patient:create"},
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
