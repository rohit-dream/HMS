"""Authentication business logic — login, refresh, logout, token validation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.database import set_rls_tenant_context
from app.core.exceptions import (
    AccountLockedError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.security import (
    AccessTokenClaims,
    create_access_token,
    decode_access_token,
    denylist_access_token,
    generate_refresh_token,
    hash_refresh_token,
    is_token_denied,
    refresh_token_expires_at,
    verify_password,
)
from app.core.tenant.resolver import resolve_tenant_for_login
from app.core.tenant.context import set_request_tenant_id
from app.core.permissions import PermissionResolver
from app.domains.identity.repositories.session_repository import SessionRepository
from app.domains.identity.repositories.tenant_repository import TenantRepository
from app.domains.identity.repositories.user_repository import UserRepository
from app.domains.identity.schemas.auth import (
    LoginResponseData,
    MeResponseData,
    TokenResponseData,
    UserSummary,
)
from app.models.core.user import User
from app.models.core.user_session import UserSession


@dataclass(frozen=True)
class AuthenticatedUser:
    """Resolved identity from validated access token."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str]
    jti: uuid.UUID
    token_exp: datetime


class AuthService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def login(
        self,
        *,
        request: Request,
        email: str,
        password: str,
    ) -> tuple[LoginResponseData, str]:
        """Authenticate user and return access token payload + opaque refresh token."""
        tenant = resolve_tenant_for_login(self.db, request, self.settings)
        set_request_tenant_id(tenant.id)
        set_rls_tenant_context(self.db, tenant.id)
        user_repo = UserRepository(self.db, tenant.id)
        session_repo = SessionRepository(self.db, tenant.id)

        user = user_repo.get_by_email(email)
        if user is None:
            raise UnauthorizedError("Invalid credentials")

        user = user_repo.unlock_if_expired(user)

        if user.is_locked:
            raise AccountLockedError("Account is temporarily locked. Try again later.")

        if user.status != "active":
            raise UnauthorizedError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            user_repo.record_failed_login(user)
            self.db.commit()
            if user.failed_login_attempts >= 5 or user.status == "locked":
                raise AccountLockedError("Account is temporarily locked. Try again later.")
            raise UnauthorizedError("Invalid credentials")

        user_repo.record_successful_login(user)
        session_repo.enforce_session_limit(user.id)

        roles = self._get_user_roles(tenant.id, user.id)
        access_token, _jti, expires_in = create_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            roles=roles,
            settings=self.settings,
        )

        refresh_token = generate_refresh_token()
        session_repo.create_session(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_token_expires_at(self.settings),
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        self.db.commit()

        return (
            LoginResponseData(
                access_token=access_token,
                expires_in=expires_in,
                user=_user_summary(user, roles),
            ),
            refresh_token,
        )

    def refresh(
        self,
        *,
        request: Request,
        refresh_token: str,
    ) -> tuple[TokenResponseData, str, uuid.UUID]:
        """Rotate refresh token and issue new access token."""
        _validate_refresh_origin(request, self.settings)
        token_hash = hash_refresh_token(refresh_token)

        revoked_session = self.db.scalars(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.isnot(None),
            )
        ).first()

        if revoked_session is not None:
            session_repo = SessionRepository(self.db, revoked_session.tenant_id)
            session_repo.revoke_all_for_user(revoked_session.user_id)
            self.db.commit()
            raise UnauthorizedError("Session invalidated. Please log in again.")

        session = self.db.scalars(
            select(UserSession).where(
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.deleted_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        ).first()

        if session is None:
            raise UnauthorizedError("Invalid or expired refresh token")

        tenant_repo = TenantRepository(self.db)
        tenant = tenant_repo.get_by_id(session.tenant_id)
        if tenant is None or not tenant.is_login_allowed:
            raise ForbiddenError("Tenant is not available")

        user_repo = UserRepository(self.db, session.tenant_id)
        user = user_repo.get_by_id(session.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User account is not active")

        session_repo = SessionRepository(self.db, session.tenant_id)
        session_repo.revoke_session(session)

        roles = self._get_user_roles(session.tenant_id, user.id)
        access_token, _jti, expires_in = create_access_token(
            user_id=user.id,
            tenant_id=session.tenant_id,
            roles=roles,
            settings=self.settings,
        )

        new_refresh = generate_refresh_token()
        session_repo.create_session(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(new_refresh),
            expires_at=refresh_token_expires_at(self.settings),
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        self.db.commit()

        return (
            TokenResponseData(access_token=access_token, expires_in=expires_in),
            new_refresh,
            session.tenant_id,
        )

    def logout(
        self,
        *,
        claims: AccessTokenClaims,
        refresh_token: str | None,
    ) -> None:
        """Invalidate access token (denylist) and revoke refresh session."""
        denylist_access_token(claims.jti, claims.exp, self.settings)

        if refresh_token:
            token_hash = hash_refresh_token(refresh_token)
            session = self.db.scalars(
                select(UserSession).where(
                    UserSession.tenant_id == claims.tenant_id,
                    UserSession.refresh_token_hash == token_hash,
                    UserSession.revoked_at.is_(None),
                )
            ).first()
            if session:
                session_repo = SessionRepository(self.db, claims.tenant_id)
                session_repo.revoke_session(session)
                self.db.commit()

    def validate_access_token(self, token: str) -> AuthenticatedUser:
        """Validate JWT signature, expiry, denylist, and tenant status."""
        try:
            claims = decode_access_token(token, self.settings)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc

        if is_token_denied(claims.jti, self.settings):
            raise UnauthorizedError("Token has been revoked")

        tenant_repo = TenantRepository(self.db)
        tenant = tenant_repo.get_by_id(claims.tenant_id)
        if tenant is None:
            raise UnauthorizedError("Invalid tenant context")
        if not tenant.is_login_allowed:
            raise ForbiddenError("Tenant is not available")

        user_repo = UserRepository(self.db, claims.tenant_id)
        user = user_repo.get_by_id(claims.sub)
        if user is None or not user.is_active:
            raise UnauthorizedError("User account is not active")

        return AuthenticatedUser(
            user_id=claims.sub,
            tenant_id=claims.tenant_id,
            roles=list(claims.roles),
            jti=claims.jti,
            token_exp=claims.exp,
        )

    def get_me(self, auth_user: AuthenticatedUser) -> MeResponseData:
        """Return current user profile with DB-resolved roles and permissions."""
        user_repo = UserRepository(self.db, auth_user.tenant_id)
        user = user_repo.get_by_id(auth_user.user_id)
        if user is None:
            raise NotFoundError("User not found")

        resolver = PermissionResolver(self.db, self.settings)
        roles = resolver.get_role_codes(auth_user.tenant_id, auth_user.user_id)
        permissions = resolver.get_permissions(auth_user.tenant_id, auth_user.user_id)

        return MeResponseData(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles,
            permissions=permissions,
            tenant_id=user.tenant_id,
            staff_id=user.staff_id,
            location_id=user.location_id,
        )

    def _get_user_roles(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> list[str]:
        """Load role codes for JWT (UI hints; DB is source of truth for /me)."""
        return PermissionResolver(self.db, self.settings).get_role_codes(tenant_id, user_id)


def _user_summary(user: User, roles: list[str]) -> UserSummary:
    return UserSummary(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=roles,
        tenant_id=user.tenant_id,
    )


def _client_ip(request: Request) -> str | None:
    host = request.client.host if request.client else None
    if not host:
        return None
    try:
        import ipaddress

        ipaddress.ip_address(host)
        return host
    except ValueError:
        return None


def _validate_refresh_origin(request: Request, settings: Settings) -> None:
    """CSRF mitigation for cookie-based refresh."""
    origin = request.headers.get("origin")
    if not origin:
        if settings.is_development:
            return
        raise UnauthorizedError("Origin header required")

    if origin not in settings.cors_origin_list:
        raise UnauthorizedError("Invalid origin")
