"""Patient endpoints — tenant-scoped patient CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import pagination_params
from app.api.v1.patient_deps import get_patient_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.database import get_db
from app.core.response import paginated_response, success_response
from app.domains.patients.schemas.allergy import AllergyCreateRequest
from app.domains.patients.schemas.chronic_condition import ChronicConditionCreateRequest
from app.domains.patients.schemas.contact import ContactCreateRequest
from app.domains.patients.schemas.patient import PatientCreateRequest, PatientUpdateRequest
from app.domains.patients.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients(
    request: Request,
    search: str | None = Query(default=None, description="Name, phone, MRN, or email"),
    location_id: uuid.UUID | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """List and search patients — requires patient:read."""
    items, total = service.list_patients(
        search=search,
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_patient(
    request: Request,
    payload: PatientCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("patient:create")),
    service: PatientService = Depends(get_patient_service),
) -> JSONResponse:
    """Register a new patient — requires patient:create."""
    data = service.create_patient(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/check-duplicate")
def check_duplicate_patients(
    request: Request,
    phone: str | None = Query(default=None, description="10-digit phone to match"),
    first_name: str | None = Query(default=None, description="First name for fuzzy match"),
    last_name: str | None = Query(default=None, description="Last name for fuzzy match"),
    exclude_patient_id: uuid.UUID | None = Query(
        default=None,
        description="Patient ID to exclude (e.g. during update)",
    ),
    ctx: AuthorizationContext = Depends(require_permission("patient:create")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """Check for potential duplicate patients — requires patient:create."""
    data = service.check_duplicates(
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        exclude_patient_id=exclude_patient_id,
    )
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.get("/{patient_id}")
def get_patient(
    request: Request,
    patient_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
    service: PatientService = Depends(get_patient_service),
    db: Session = Depends(get_db),
) -> dict:
    """Get patient profile — requires patient:read."""
    from app.domains.audit.services.audit_service import AuditService

    data = service.get_patient(patient_id)
    AuditService(db).record_phi_access(
        tenant_id=ctx.user.tenant_id,
        patient_id=patient_id,
        user_id=ctx.user.user_id,
        request=request,
    )
    db.commit()
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{patient_id}")
def update_patient(
    request: Request,
    patient_id: uuid.UUID,
    payload: PatientUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("patient:update")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """Update patient demographics — requires patient:update."""
    data = service.update_patient(patient_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("patient:delete")),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    """Soft-delete a patient — requires patient:delete."""
    service.delete_patient(patient_id, actor_id=ctx.user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/allergies")
def list_patient_allergies(
    request: Request,
    patient_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """List patient allergies — requires patient:read."""
    items = service.list_allergies(patient_id)
    return success_response(
        data=[item.model_dump(mode="json") for item in items],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{patient_id}/allergies", status_code=status.HTTP_201_CREATED)
def add_patient_allergy(
    request: Request,
    patient_id: uuid.UUID,
    payload: AllergyCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("patient:update")),
    service: PatientService = Depends(get_patient_service),
) -> JSONResponse:
    """Add a patient allergy — requires patient:update."""
    data = service.add_allergy(patient_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.delete("/{patient_id}/allergies/{allergy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_allergy(
    patient_id: uuid.UUID,
    allergy_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("patient:update")),
    service: PatientService = Depends(get_patient_service),
) -> Response:
    """Soft-delete a patient allergy — requires patient:update."""
    service.delete_allergy(patient_id, allergy_id, actor_id=ctx.user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{patient_id}/contacts")
def list_patient_contacts(
    request: Request,
    patient_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """List patient contacts — requires patient:read."""
    items = service.list_contacts(patient_id)
    return success_response(
        data=[item.model_dump(mode="json") for item in items],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{patient_id}/contacts", status_code=status.HTTP_201_CREATED)
def add_patient_contact(
    request: Request,
    patient_id: uuid.UUID,
    payload: ContactCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("patient:update")),
    service: PatientService = Depends(get_patient_service),
) -> JSONResponse:
    """Add a patient contact — requires patient:update."""
    data = service.add_contact(patient_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/{patient_id}/visits")
def list_patient_visits(
    request: Request,
    patient_id: uuid.UUID,
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """List patient visit history — requires patient:read."""
    items, total = service.list_visit_history(
        patient_id,
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


@router.get("/{patient_id}/chronic-conditions")
def list_chronic_conditions(
    request: Request,
    patient_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("patient:read")),
    service: PatientService = Depends(get_patient_service),
) -> dict:
    """List patient chronic conditions — requires patient:read."""
    items = service.list_chronic_conditions(patient_id)
    return success_response(
        data=[item.model_dump(mode="json") for item in items],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{patient_id}/chronic-conditions", status_code=status.HTTP_201_CREATED)
def add_chronic_condition(
    request: Request,
    patient_id: uuid.UUID,
    payload: ChronicConditionCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("patient:update")),
    service: PatientService = Depends(get_patient_service),
) -> JSONResponse:
    """Record a chronic condition — requires patient:update."""
    data = service.add_chronic_condition(patient_id, payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)
