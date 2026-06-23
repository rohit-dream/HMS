"""Doctor schedules API — weekly availability slots per doctor."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.admin_deps import get_doctor_schedule_service
from app.api.v1.deps import pagination_params
from app.core.authorization import AuthorizationContext, require_any_permission, require_permission
from app.core.response import paginated_response, success_response
from app.domains.org.schemas.doctor_schedule import (
    DoctorScheduleCreateRequest,
    DoctorScheduleUpdateRequest,
)
from app.domains.org.services.doctor_schedule_service import DoctorScheduleService

router = APIRouter(prefix="/doctors/{doctor_id}/schedules", tags=["doctor-schedules"])

_READ_PERMISSIONS = ("patient:read", "admin:doctors", "appointment:read")


@router.get("")
def list_doctor_schedules(
    request: Request,
    doctor_id: uuid.UUID,
    day_of_week: int | None = Query(default=None, ge=0, le=6),
    is_active: bool | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_any_permission(*_READ_PERMISSIONS)),
    service: DoctorScheduleService = Depends(get_doctor_schedule_service),
) -> dict:
    """List weekly schedule slots for a doctor."""
    items, total = service.list_schedules(
        doctor_id,
        day_of_week=day_of_week,
        is_active=is_active,
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
def create_doctor_schedule(
    request: Request,
    doctor_id: uuid.UUID,
    payload: DoctorScheduleCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:doctors")),
    service: DoctorScheduleService = Depends(get_doctor_schedule_service),
) -> JSONResponse:
    """Add a weekly schedule slot for a doctor."""
    data = service.create_schedule(doctor_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/{schedule_id}")
def get_doctor_schedule(
    request: Request,
    doctor_id: uuid.UUID,
    schedule_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_any_permission(*_READ_PERMISSIONS)),
    service: DoctorScheduleService = Depends(get_doctor_schedule_service),
) -> dict:
    """Get a single schedule slot."""
    data = service.get_schedule(doctor_id, schedule_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{schedule_id}")
def update_doctor_schedule(
    request: Request,
    doctor_id: uuid.UUID,
    schedule_id: uuid.UUID,
    payload: DoctorScheduleUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:doctors")),
    service: DoctorScheduleService = Depends(get_doctor_schedule_service),
) -> dict:
    """Update a schedule slot."""
    data = service.update_schedule(
        doctor_id,
        schedule_id,
        payload,
        actor_id=ctx.user.user_id,
    )
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{schedule_id}")
def delete_doctor_schedule(
    request: Request,
    doctor_id: uuid.UUID,
    schedule_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:doctors")),
    service: DoctorScheduleService = Depends(get_doctor_schedule_service),
) -> dict:
    """Soft-delete a schedule slot."""
    data = service.delete_schedule(doctor_id, schedule_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
