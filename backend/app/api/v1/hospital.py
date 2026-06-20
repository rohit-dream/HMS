"""Hospital management — organization profile, branches, settings."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from app.api.v1.platform_deps import get_hospital_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response
from app.domains.platform.schemas.tenant import (
    HospitalProfileUpdateRequest,
    LocationCreateRequest,
    LocationUpdateRequest,
    SettingUpsertRequest,
    SettingsBulkUpdateRequest,
)
from app.domains.platform.services.hospital_service import HospitalService

router = APIRouter(prefix="/hospital", tags=["hospital"])


@router.get("/profile")
def get_hospital_profile(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """Get organization (hospital) profile for current tenant."""
    data = service.get_profile()
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/profile")
def update_hospital_profile(
    request: Request,
    payload: HospitalProfileUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """Update organization profile — name, address, tax ID, branding."""
    data = service.update_profile(payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/locations")
def list_locations(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """List hospital branches for current tenant."""
    data = service.list_locations()
    return success_response(
        data=[item.model_dump(mode="json") for item in data],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/locations", status_code=201)
def create_location(
    request: Request,
    payload: LocationCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """Create a hospital branch."""
    data = service.create_location(payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/locations/{location_id}")
def update_location(
    request: Request,
    location_id: uuid.UUID,
    payload: LocationUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """Update a hospital branch."""
    data = service.update_location(location_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/settings")
def list_settings(
    request: Request,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """List tenant configuration settings."""
    data = service.list_settings()
    return success_response(
        data=[item.model_dump(mode="json") for item in data],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.put("/settings/{setting_key}")
def upsert_setting(
    request: Request,
    setting_key: str,
    payload: SettingUpsertRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """Create or update a single tenant setting."""
    data = service.upsert_setting(setting_key, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/settings")
def bulk_update_settings(
    request: Request,
    payload: SettingsBulkUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:settings")),
    service: HospitalService = Depends(get_hospital_service),
) -> dict:
    """Bulk update multiple tenant settings."""
    data = service.bulk_update_settings(payload, actor_id=ctx.user.user_id)
    return success_response(
        data=[item.model_dump(mode="json") for item in data],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
