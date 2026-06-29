"""OPD prescription endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.opd_deps import get_opd_prescription_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response
from app.domains.clinical.schemas.opd.prescription import OpdPrescriptionCreateRequest
from app.domains.clinical.services.opd_prescription_service import OpdPrescriptionService

router = APIRouter(prefix="/visits/{visit_id}/prescriptions")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_prescription(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdPrescriptionCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:prescribe")),
    service: OpdPrescriptionService = Depends(get_opd_prescription_service),
) -> JSONResponse:
    """Create e-prescription with line items."""
    data = service.create_prescription(visit_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("")
def list_prescriptions(
    request: Request,
    visit_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("opd:read")),
    service: OpdPrescriptionService = Depends(get_opd_prescription_service),
) -> dict:
    """List prescriptions for a visit."""
    data = service.list_prescriptions(visit_id)
    return success_response(
        data=[item.model_dump(mode="json") for item in data],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/{prescription_id}")
def get_prescription(
    request: Request,
    visit_id: uuid.UUID,
    prescription_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("opd:read")),
    service: OpdPrescriptionService = Depends(get_opd_prescription_service),
) -> dict:
    """Get prescription detail with items."""
    data = service.get_prescription(visit_id, prescription_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
