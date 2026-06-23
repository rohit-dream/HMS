"""Staff API — tenant-scoped employee CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.admin_deps import get_staff_service
from app.api.v1.deps import pagination_params
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import paginated_response, success_response
from app.domains.org.schemas.staff import StaffCreateRequest, StaffUpdateRequest
from app.domains.org.services.staff_service import StaffService

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("")
def list_staff(
    request: Request,
    search: str | None = Query(default=None, description="Search name, email, or employee code"),
    status: str | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    location_id: uuid.UUID | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("admin:staff")),
    service: StaffService = Depends(get_staff_service),
) -> dict:
    """List employees for the current tenant."""
    items, total = service.list_staff(
        query=search,
        status=status,
        department_id=department_id,
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
def create_staff(
    request: Request,
    payload: StaffCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:staff")),
    service: StaffService = Depends(get_staff_service),
) -> JSONResponse:
    """Create an employee record."""
    data = service.create_staff(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/{staff_id}")
def get_staff(
    request: Request,
    staff_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:staff")),
    service: StaffService = Depends(get_staff_service),
) -> dict:
    """Get an employee by ID."""
    data = service.get_staff(staff_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{staff_id}")
def update_staff(
    request: Request,
    staff_id: uuid.UUID,
    payload: StaffUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:staff")),
    service: StaffService = Depends(get_staff_service),
) -> dict:
    """Update an employee record."""
    data = service.update_staff(staff_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{staff_id}")
def delete_staff(
    request: Request,
    staff_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:staff")),
    service: StaffService = Depends(get_staff_service),
) -> dict:
    """Soft-delete an employee (status set to terminated)."""
    data = service.delete_staff(staff_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
