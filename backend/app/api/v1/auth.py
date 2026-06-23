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
from app.domains.identity.schemas.auth import (
    AcceptInviteRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponseData,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.domains.identity.schemas.user import SelfProfileUpdateRequest
from app.domains.identity.services.auth_service import AuthenticatedUser, AuthService
from app.domains.identity.services.user_management_service import UserManagementService

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
    AuthService(db, settings).logout(
        claims=claims,
        refresh_token=refresh_value,
        request=request,
    )

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


@router.patch("/me")
def update_me(
    request: Request,
    payload: SelfProfileUpdateRequest,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update own profile (name, phone, avatar)."""
    service = UserManagementService(db, auth_user.tenant_id)
    data = service.update_self_profile(auth_user.user_id, payload)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=auth_user.tenant_id,
    )


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Request a password reset link (always returns success to prevent enumeration)."""
    check_auth_rate_limit(request, settings)
    message = AuthService(db, settings).forgot_password(
        request=request,
        email=str(payload.email).lower(),
    )
    return success_response(
        data=MessageResponseData(message=message).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Reset password using a one-time token from email."""
    check_auth_rate_limit(request, settings)
    message = AuthService(db, settings).reset_password(
        token=payload.token,
        new_password=payload.new_password,
        request=request,
    )
    return success_response(
        data=MessageResponseData(message=message).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/accept-invite", response_model=None)
def accept_invite(
    payload: AcceptInviteRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Activate invited user with password and issue login tokens."""
    check_auth_rate_limit(request, settings)
    data, refresh_token = AuthService(db, settings).accept_invite(
        invite_token=payload.invite_token,
        password=payload.password,
        request=request,
    )
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=data.user.tenant_id,
    )
    json_response = JSONResponse(content=body)
    _set_refresh_cookie(json_response, refresh_token, settings)
    return json_response


@router.post("/verify-email")
def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Verify email address using a one-time token from email."""
    check_auth_rate_limit(request, settings)
    message = AuthService(db, settings).verify_email(token=payload.token)
    return success_response(
        data=MessageResponseData(message=message).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/resend-verification")
def resend_verification(
    request: Request,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Resend email verification link to the authenticated user."""
    check_auth_rate_limit(request, settings)
    message = AuthService(db, settings).resend_verification(auth_user=auth_user)
    return success_response(
        data=MessageResponseData(message=message).model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=auth_user.tenant_id,
    )
