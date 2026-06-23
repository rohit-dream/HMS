"""Doctors API — clinical profiles linked to staff."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.admin_deps import get_doctor_service
from app.api.v1.deps import pagination_params
from app.core.authorization import AuthorizationContext, require_any_permission, require_permission
from app.core.response import paginated_response, success_response
from app.domains.org.schemas.doctor import DoctorCreateRequest, DoctorUpdateRequest
from app.domains.org.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["doctors"])

_READ_PERMISSIONS = ("patient:read", "admin:doctors", "appointment:read")


@router.get("")
def list_doctors(
    request: Request,
    search: str | None = Query(default=None, description="Search name or specialization"),
    specialization: str | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    location_id: uuid.UUID | None = Query(default=None),
    is_available: bool | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_any_permission(*_READ_PERMISSIONS)),
    service: DoctorService = Depends(get_doctor_service),
) -> dict:
    """List doctors for booking and admin."""
    items, total = service.list_doctors(
        query=search,
        specialization=specialization,
        department_id=department_id,
        location_id=location_id,
        is_available=is_available,
        page=pagination["page"],
        page_size=pagination["page_size"],
    )
    return paginated_response(
        data=[item.model_dump(mode="json") for item in items],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
        page=pagination["page"],
        page_size=pagination["page_size"],
        total_items=total,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_doctor(
    request: Request,
    payload: DoctorCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:doctors")),
    service: DoctorService = Depends(get_doctor_service),
) -> JSONResponse:
    """Create a doctor profile for an existing staff member."""
    data = service.create_doctor(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/{doctor_id}")
def get_doctor(
    request: Request,
    doctor_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_any_permission(*_READ_PERMISSIONS)),
    service: DoctorService = Depends(get_doctor_service),
) -> dict:
    """Get a doctor profile by ID."""
    data = service.get_doctor(doctor_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{doctor_id}")
def update_doctor(
    request: Request,
    doctor_id: uuid.UUID,
    payload: DoctorUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:doctors")),
    service: DoctorService = Depends(get_doctor_service),
) -> dict:
    """Update a doctor profile."""
    data = service.update_doctor(doctor_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{doctor_id}")
def delete_doctor(
    request: Request,
    doctor_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:doctors")),
    service: DoctorService = Depends(get_doctor_service),
) -> dict:
    """Soft-delete a doctor profile."""
    data = service.delete_doctor(doctor_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
