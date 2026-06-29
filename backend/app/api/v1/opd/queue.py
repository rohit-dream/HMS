"""OPD queue endpoints."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.v1.opd_deps import get_opd_queue_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response
from app.domains.clinical.schemas.opd.queue import (
    OpdQueueCreateRequest,
    OpdQueueSkipRequest,
    OpdQueueUpdateRequest,
)
from app.domains.clinical.services.opd_queue_service import OpdQueueService

router = APIRouter()


@router.get("/queue/poll", response_model=None)
def poll_queue_board(
    request: Request,
    response: Response,
    doctor_id: uuid.UUID = Query(..., description="Doctor whose queue to poll"),
    queue_date: date | None = Query(default=None, alias="date", description="Queue date"),
    location_id: uuid.UUID | None = Query(default=None),
    queue_status: str | None = Query(default=None, alias="status"),
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> Response | dict:
    """Poll doctor queue with ETag support (recommended interval: 5 seconds)."""
    data, etag = service.poll_queue_board(
        doctor_id=doctor_id,
        queue_date=queue_date,
        location_id=location_id,
        status=queue_status,
        if_none_match=if_none_match,
    )
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = "no-cache"

    if data is None:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={"ETag": f'"{etag}"', "Cache-Control": "no-cache"},
        )

    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/queue")
def get_queue_board(
    request: Request,
    doctor_id: uuid.UUID = Query(..., description="Doctor whose queue to fetch"),
    queue_date: date | None = Query(default=None, alias="date", description="Queue date"),
    location_id: uuid.UUID | None = Query(default=None),
    queue_status: str | None = Query(default=None, alias="status"),
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> dict:
    """Poll doctor queue for a date."""
    data = service.get_queue_board(
        doctor_id=doctor_id,
        queue_date=queue_date,
        location_id=location_id,
        status=queue_status,
    )
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/queue", status_code=status.HTTP_201_CREATED)
def add_to_queue(
    request: Request,
    payload: OpdQueueCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> JSONResponse:
    """Add visit to doctor queue."""
    data = service.add_to_queue(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.patch("/queue/{queue_id}")
def update_queue_entry(
    request: Request,
    queue_id: uuid.UUID,
    payload: OpdQueueUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> dict:
    """Reorder queue or change priority."""
    data = service.update_queue_entry(queue_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/queue/{queue_id}/call")
def call_queue_patient(
    request: Request,
    queue_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> dict:
    """Call next patient in queue."""
    data = service.call_patient(queue_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/queue/{queue_id}/complete")
def complete_queue_entry(
    request: Request,
    queue_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> dict:
    """Mark queue entry complete."""
    data = service.complete_queue_entry(queue_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/queue/{queue_id}/skip")
def skip_queue_patient(
    request: Request,
    queue_id: uuid.UUID,
    payload: OpdQueueSkipRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:queue")),
    service: OpdQueueService = Depends(get_opd_queue_service),
) -> dict:
    """Skip patient in queue."""
    data = service.skip_patient(queue_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
