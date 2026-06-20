"""Platform tenant management — provisioning, activation, suspension."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.platform_deps import get_tenant_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response
from app.domains.platform.schemas.tenant import (
    TenantCreateRequest,
    TenantRegisterRequest,
    TenantStatusActionRequest,
)
from app.domains.platform.services.tenant_service import TenantService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_tenant(
    request: Request,
    payload: TenantRegisterRequest,
    service: TenantService = Depends(get_tenant_service),
) -> JSONResponse:
    """
    Public self-service tenant registration.

    Provisions tenant, RBAC, primary location, settings, and hospital_owner user.
    """
    data = service.register_tenant(payload)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=data.tenant.id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
def create_tenant(
    request: Request,
    payload: TenantCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("platform:update")),
    service: TenantService = Depends(get_tenant_service),
) -> JSONResponse:
    """Platform-admin tenant creation (no owner user)."""
    data = service.create_tenant(payload)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=data.id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/tenants/{tenant_id}")
def get_tenant(
    request: Request,
    tenant_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("platform:read")),
    service: TenantService = Depends(get_tenant_service),
) -> dict:
    """Platform-admin tenant detail."""
    data = service.get_tenant(tenant_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/tenants/{tenant_id}/activate")
def activate_tenant(
    request: Request,
    tenant_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("platform:update")),
    service: TenantService = Depends(get_tenant_service),
) -> dict:
    """Activate a trial, suspended, or past_due tenant."""
    data = service.activate_tenant(tenant_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/tenants/{tenant_id}/suspend")
def suspend_tenant(
    request: Request,
    tenant_id: uuid.UUID,
    payload: TenantStatusActionRequest | None = None,
    ctx: AuthorizationContext = Depends(require_permission("platform:update")),
    service: TenantService = Depends(get_tenant_service),
) -> dict:
    """Suspend a tenant — blocks login and new operations."""
    reason = payload.reason if payload else None
    data = service.suspend_tenant(tenant_id, actor_id=ctx.user.user_id, reason=reason)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
