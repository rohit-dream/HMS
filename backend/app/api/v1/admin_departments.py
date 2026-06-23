"""Admin departments API — tenant-scoped CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.admin_deps import get_department_service
from app.api.v1.deps import pagination_params
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import paginated_response, success_response
from app.domains.org.schemas.department import DepartmentCreateRequest, DepartmentUpdateRequest
from app.domains.org.services.department_service import DepartmentService

router = APIRouter(prefix="/admin/departments", tags=["admin-departments"])


@router.get("")
def list_departments(
    request: Request,
    q: str | None = Query(default=None, description="Search name or code"),
    is_active: bool | None = Query(default=None),
    location_id: uuid.UUID | None = Query(default=None),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("admin:departments")),
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    """List departments for the current tenant."""
    items, total = service.list_departments(
        query=q,
        is_active=is_active,
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
def create_department(
    request: Request,
    payload: DepartmentCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:departments")),
    service: DepartmentService = Depends(get_department_service),
) -> JSONResponse:
    """Create a hospital department."""
    data = service.create_department(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/{department_id}")
def get_department(
    request: Request,
    department_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:departments")),
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    """Get a department by ID."""
    data = service.get_department(department_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{department_id}")
def update_department(
    request: Request,
    department_id: uuid.UUID,
    payload: DepartmentUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:departments")),
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    """Update a department."""
    data = service.update_department(department_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{department_id}")
def delete_department(
    request: Request,
    department_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:departments")),
    service: DepartmentService = Depends(get_department_service),
) -> dict:
    """Soft-delete a department."""
    data = service.delete_department(department_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
