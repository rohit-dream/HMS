"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.auth_deps import get_auth_service, get_current_user
from app.core.config import Settings, get_settings
from app.core.constants import REFRESH_TOKEN_COOKIE
from app.core.database import get_db
from app.core.rate_limit import check_auth_rate_limit
from app.core.response import success_response
from app.core.security import decode_access_token
from app.domains.identity.schemas.auth import LoginRequest
from app.domains.identity.services.auth_service import AuthenticatedUser, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(
    response: Response,
    token: str,
    settings: Settings,
) -> None:
    max_age = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path=f"{settings.api_v1_prefix}/auth",
        max_age=max_age,
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        path=f"{settings.api_v1_prefix}/auth",
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
    )


@router.post("/login", response_model=None)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Tenant-scoped email/password login."""
    check_auth_rate_limit(request, settings)
    auth_service = AuthService(db, settings)
    data, refresh_token = auth_service.login(
        request=request,
        email=str(payload.email).lower(),
        password=payload.password,
    )
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=data.user.tenant_id,
    )
    json_response = JSONResponse(content=body)
    _set_refresh_cookie(json_response, refresh_token, settings)
    return json_response


@router.post("/refresh", response_model=None)
def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Issue new access token using HttpOnly refresh cookie."""
    check_auth_rate_limit(request, settings)
    refresh_value = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not refresh_value:
        from app.core.exceptions import UnauthorizedError

        raise UnauthorizedError("Refresh token missing")

    auth_service = AuthService(db, settings)
    data, new_refresh, tenant_id = auth_service.refresh(
        request=request,
        refresh_token=refresh_value,
    )
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=tenant_id,
    )
    json_response = JSONResponse(content=body)
    _set_refresh_cookie(json_response, new_refresh, settings)
    return json_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Revoke current session and denylist access token."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    claims = decode_access_token(token, settings)

    refresh_value = request.cookies.get(REFRESH_TOKEN_COOKIE)
    AuthService(db, settings).logout(claims=claims, refresh_token=refresh_value)

    _clear_refresh_cookie(response, settings)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me")
def get_me(
    request: Request,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Return authenticated user profile."""
    data = auth_service.get_me(auth_user)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=auth_user.tenant_id,
    )
