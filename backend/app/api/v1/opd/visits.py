"""OPD visit endpoints."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import pagination_params
from app.api.v1.opd_deps import get_opd_visit_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.database import get_db
from app.core.response import paginated_response, success_response
from app.domains.clinical.schemas.opd.visit import (
    OpdVisitCancelRequest,
    OpdVisitCompleteRequest,
    OpdVisitCreateRequest,
    OpdVisitStartRequest,
    OpdVisitUpdateRequest,
)
from app.domains.clinical.services.opd_visit_service import OpdVisitService

router = APIRouter()


@router.post("/visits", status_code=status.HTTP_201_CREATED)
def create_visit(
    request: Request,
    payload: OpdVisitCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:create")),
    service: OpdVisitService = Depends(get_opd_visit_service),
) -> JSONResponse:
    """Create OPD visit (walk-in or appointment-linked)."""
    data = service.create_visit(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/visits")
def list_visits(
    request: Request,
    doctor_id: uuid.UUID | None = Query(default=None),
    patient_id: uuid.UUID | None = Query(default=None),
    visit_date: date | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    status: str | None = Query(default=None),
    visit_type: str | None = Query(default=None),
    location_id: uuid.UUID | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("opd:read")),
    service: OpdVisitService = Depends(get_opd_visit_service),
) -> dict:
    """List OPD visits with filters."""
    items, total = service.list_visits(
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=visit_date,
        from_date=from_date,
        to_date=to_date,
        status=status,
        visit_type=visit_type,
        location_id=location_id,
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


@router.get("/visits/{visit_id}")
def get_visit(
    request: Request,
    visit_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("opd:read")),
    service: OpdVisitService = Depends(get_opd_visit_service),
    db: Session = Depends(get_db),
) -> dict:
    """Get OPD visit detail."""
    from app.core.database import set_rls_tenant_context
    from app.domains.audit.services.audit_service import AuditService

    data = service.get_visit(visit_id)
    set_rls_tenant_context(db, ctx.user.tenant_id)
    AuditService(db).record_opd_visit_phi_access(
        tenant_id=ctx.user.tenant_id,
        patient_id=data.patient_id,
        visit_id=visit_id,
        user_id=ctx.user.user_id,
        request=request,
    )
    db.commit()
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/visits/{visit_id}")
def update_visit(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdVisitUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:update")),
    service: OpdVisitService = Depends(get_opd_visit_service),
) -> dict:
    """Update visit metadata before consultation."""
    data = service.update_visit(visit_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/visits/{visit_id}/cancel")
def cancel_visit(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdVisitCancelRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:update")),
    service: OpdVisitService = Depends(get_opd_visit_service),
) -> dict:
    """Cancel OPD visit."""
    data = service.cancel_visit(visit_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/visits/{visit_id}/start")
def start_visit(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdVisitStartRequest | None = None,
    ctx: AuthorizationContext = Depends(require_permission("opd:consult")),
    service: OpdVisitService = Depends(get_opd_visit_service),
) -> dict:
    """Start doctor consultation."""
    data = service.start_visit(visit_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/visits/{visit_id}/complete")
def complete_visit(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdVisitCompleteRequest | None = None,
    ctx: AuthorizationContext = Depends(require_permission("opd:consult")),
    service: OpdVisitService = Depends(get_opd_visit_service),
) -> dict:
    """Complete consultation and finalize visit."""
    data = service.complete_visit(visit_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
