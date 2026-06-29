"""OPD vitals endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.opd_deps import get_opd_vitals_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response
from app.domains.clinical.schemas.opd.vitals import OpdVitalsCreateRequest
from app.domains.clinical.services.opd_vitals_service import OpdVitalsService

router = APIRouter(prefix="/visits/{visit_id}/vitals")


@router.post("", status_code=status.HTTP_201_CREATED)
def record_vitals(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdVitalsCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:consult")),
    service: OpdVitalsService = Depends(get_opd_vitals_service),
) -> JSONResponse:
    """Record vitals during consultation."""
    data = service.record_vitals(visit_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("")
def list_vitals(
    request: Request,
    visit_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("opd:read")),
    service: OpdVitalsService = Depends(get_opd_vitals_service),
) -> dict:
    """List vitals for a visit."""
    data = service.list_vitals(visit_id)
    return success_response(
        data=[item.model_dump(mode="json") for item in data],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
