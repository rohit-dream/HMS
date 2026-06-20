"""Authentication dependencies — token validation and current user."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.tenant.context import clear_auth_context, set_auth_context
from app.domains.identity.services.auth_service import AuthenticatedUser, AuthService

_bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(db, settings)


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """Validate Bearer JWT and return authenticated user context."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication required")

    auth_service = AuthService(db, settings)
    auth_user = auth_service.validate_access_token(credentials.credentials)

    set_auth_context(tenant_id=auth_user.tenant_id, user_id=auth_user.user_id)
    request.state.tenant_id = str(auth_user.tenant_id)
    request.state.user_id = str(auth_user.user_id)
    return auth_user


def get_optional_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser | None:
    """Return authenticated user if Bearer token present, else None."""
    if credentials is None:
        return None
    try:
        return get_current_user(request, credentials, db, settings)
    except UnauthorizedError:
        return None
    finally:
        if credentials is None:
            clear_auth_context()
