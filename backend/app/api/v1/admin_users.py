"""Admin user management endpoints — tenant-scoped."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.admin_deps import get_user_management_service
from app.api.v1.deps import pagination_params
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import paginated_response, success_response
from app.domains.identity.schemas.user import (
    AdminResetPasswordRequest,
    AssignRoleRequest,
    UserCreateRequest,
    UserInviteRequest,
    UserUpdateRequest,
)
from app.domains.identity.services.user_management_service import UserManagementService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("")
def search_users(
    request: Request,
    q: str | None = Query(default=None, description="Search email or name"),
    user_status: str | None = Query(default=None, alias="status"),
    pagination: dict[str, int] = Depends(pagination_params),
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Search and list tenant users."""
    items, total = service.search_users(
        query=q,
        status=user_status,
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
def create_user(
    request: Request,
    payload: UserCreateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> JSONResponse:
    """Create an active user with password and optional roles."""
    data = service.create_user(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.post("/invite", status_code=status.HTTP_201_CREATED)
def invite_user(
    request: Request,
    payload: UserInviteRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> JSONResponse:
    """Invite user — created inactive until password is set."""
    data = service.invite_user(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/{user_id}")
def get_user(
    request: Request,
    user_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Get user profile by ID (tenant-scoped)."""
    data = service.get_user(user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.patch("/{user_id}")
def update_user(
    request: Request,
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Update user profile fields."""
    data = service.update_user(user_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{user_id}/disable")
def disable_user(
    request: Request,
    user_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Disable user — revokes sessions; cannot disable self or last owner."""
    data = service.disable_user(user_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{user_id}/roles")
def assign_role(
    request: Request,
    user_id: uuid.UUID,
    payload: AssignRoleRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Assign a role to a user."""
    data = service.assign_role(user_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/{user_id}/roles/{role_code}")
def remove_role(
    request: Request,
    user_id: uuid.UUID,
    role_code: str,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Remove a role from a user."""
    data = service.remove_role(user_id, role_code, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{user_id}/reset-password")
def reset_password(
    request: Request,
    user_id: uuid.UUID,
    payload: AdminResetPasswordRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Admin reset user password — revokes all sessions."""
    data = service.reset_password(user_id, payload, actor_id=ctx.user.user_id)
    return success_response(
        data=data,
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.post("/{user_id}/reset-token")
def create_reset_token(
    request: Request,
    user_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:users")),
    service: UserManagementService = Depends(get_user_management_service),
) -> dict:
    """Generate password reset token (dev workflow until email adapter exists)."""
    data = service.create_password_reset_token(user_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data,
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
