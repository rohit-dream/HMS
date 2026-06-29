"""OPD clinical notes endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.opd_deps import get_opd_clinical_note_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import success_response
from app.domains.clinical.schemas.opd.notes import OpdNoteCreateRequest, OpdNoteType
from app.domains.clinical.services.opd_clinical_note_service import OpdClinicalNoteService

router = APIRouter(prefix="/visits/{visit_id}/notes")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_note(
    request: Request,
    visit_id: uuid.UUID,
    payload: OpdNoteCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("opd:consult")),
    service: OpdClinicalNoteService = Depends(get_opd_clinical_note_service),
) -> JSONResponse:
    """Add clinical note to visit."""
    data = service.create_note(visit_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("")
def list_notes(
    request: Request,
    visit_id: uuid.UUID,
    note_type: OpdNoteType | None = Query(default=None),
    ctx: AuthorizationContext = Depends(require_permission("opd:read")),
    service: OpdClinicalNoteService = Depends(get_opd_clinical_note_service),
) -> dict:
    """List clinical notes for a visit."""
    data = service.list_notes(visit_id, note_type=note_type)
    return success_response(
        data=[item.model_dump(mode="json") for item in data],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
