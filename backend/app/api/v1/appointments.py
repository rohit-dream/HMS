"""Appointments API — tenant-scoped booking CRUD."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.v1.appointment_deps import get_appointment_service
from app.api.v1.deps import pagination_params
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import paginated_response, success_response
from app.domains.clinical.schemas.appointment import (
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
)
from app.domains.clinical.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("")
def list_appointments(
    request: Request,
    doctor_id: uuid.UUID | None = Query(default=None),
    patient_id: uuid.UUID | None = Query(default=None),
    appointment_date: date | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    status: str | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("appointment:read")),
    service: AppointmentService = Depends(get_appointment_service),
) -> dict:
    """List appointments with optional filters — requires appointment:read."""
    items, total = service.list_appointments(
        doctor_id=doctor_id,
        patient_id=patient_id,
        appointment_date=appointment_date,
        from_date=from_date,
        to_date=to_date,
        status=status,
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
def create_appointment(
    request: Request,
    payload: AppointmentCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("appointment:create")),
    service: AppointmentService = Depends(get_appointment_service),
) -> JSONResponse:
    """Book a new appointment — requires appointment:create."""
    data = service.create_appointment(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/availability")
def get_appointment_availability(
    request: Request,
    doctor_id: uuid.UUID = Query(..., description="Doctor to check availability for"),
    appointment_date: date = Query(..., alias="date", description="Date to check (ISO)"),
    location_id: uuid.UUID | None = Query(default=None),
    ctx: AuthorizationContext = Depends(require_permission("appointment:read")),
    service: AppointmentService = Depends(get_appointment_service),
) -> dict:
    """Return bookable slots for a doctor on a date — requires appointment:read."""
    data = service.get_availability(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        location_id=location_id,
    )
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/{appointment_id}")
def get_appointment(
    request: Request,
    appointment_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("appointment:read")),
    service: AppointmentService = Depends(get_appointment_service),
) -> dict:
    """Get appointment details — requires appointment:read."""
    data = service.get_appointment(appointment_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{appointment_id}/confirm")
def confirm_appointment(
    request: Request,
    appointment_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("appointment:update")),
    service: AppointmentService = Depends(get_appointment_service),
) -> dict:
    """Confirm a scheduled appointment — requires appointment:update."""
    data = service.confirm_appointment(appointment_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{appointment_id}/cancel")
def cancel_appointment(
    request: Request,
    appointment_id: uuid.UUID,
    payload: AppointmentCancelRequest,
    ctx: AuthorizationContext = Depends(require_permission("appointment:update")),
    service: AppointmentService = Depends(get_appointment_service),
) -> dict:
    """Cancel an appointment with a reason — requires appointment:update."""
    data = service.cancel_appointment(
        appointment_id,
        payload,
        actor_id=ctx.user.user_id,
    )
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{appointment_id}")
def update_appointment(
    request: Request,
    appointment_id: uuid.UUID,
    payload: AppointmentUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("appointment:update")),
    service: AppointmentService = Depends(get_appointment_service),
) -> dict:
    """Reschedule or update an appointment — requires appointment:update."""
    data = service.update_appointment(
        appointment_id,
        payload,
        actor_id=ctx.user.user_id,
    )
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(
    appointment_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("appointment:update")),
    service: AppointmentService = Depends(get_appointment_service),
) -> Response:
    """Soft-delete an appointment — requires appointment:update."""
    service.delete_appointment(appointment_id, actor_id=ctx.user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
