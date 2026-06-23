"""Authentication business logic — login, refresh, logout, token validation."""

from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.adapters.email import EmailNotificationService
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
    hash_password,
    hash_refresh_token,
    is_token_denied,
    refresh_token_expires_at,
    verify_password,
)
from app.core.tenant.resolver import resolve_tenant_for_login
from app.core.tenant.context import set_request_tenant_id
from app.core.tenant.subscription import assert_tenant_can_authenticate
from app.core.permissions import PermissionResolver
from app.domains.audit.services.audit_service import AuditService
from app.domains.identity.constants import (
    EMAIL_ALREADY_VERIFIED_MESSAGE,
    EMAIL_VERIFICATION_SUCCESS_MESSAGE,
    EMAIL_VERIFICATION_TOKEN_HOURS,
    FORGOT_PASSWORD_MESSAGE,
    PASSWORD_RESET_TOKEN_HOURS,
    RESEND_VERIFICATION_MESSAGE,
    RESET_PASSWORD_SUCCESS_MESSAGE,
)
from app.domains.identity.repositories.email_verification_repository import EmailVerificationRepository
from app.domains.identity.repositories.password_reset_repository import PasswordResetRepository
from app.domains.identity.repositories.session_repository import SessionRepository
from app.domains.identity.repositories.tenant_repository import TenantRepository
from app.domains.identity.repositories.user_invite_repository import UserInviteRepository
from app.domains.identity.repositories.user_repository import UserRepository
from app.domains.identity.schemas.auth import (
    LoginResponseData,
    MeResponseData,
    TokenResponseData,
    UserSummary,
)
from app.models.core.user import User
from app.models.core.user_session import UserSession

logger = logging.getLogger(__name__)


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
        self._email = EmailNotificationService(self.settings)

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
        audit = AuditService(self.db)
        if user is None:
            audit.record_login_failed(tenant_id=tenant.id, user_id=None, request=request)
            self.db.commit()
            raise UnauthorizedError("Invalid credentials")

        user = user_repo.unlock_if_expired(user)

        if user.is_locked:
            audit.record_account_lockout(
                tenant_id=tenant.id,
                user_id=user.id,
                request=request,
                attempts=user.failed_login_attempts,
            )
            self.db.commit()
            raise AccountLockedError("Account is temporarily locked. Try again later.")

        if user.status != "active":
            audit.record_login_failed(tenant_id=tenant.id, user_id=user.id, request=request)
            self.db.commit()
            raise UnauthorizedError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            user_repo.record_failed_login(user)
            if user.failed_login_attempts >= 5 or user.status == "locked":
                audit.record_account_lockout(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    request=request,
                    attempts=user.failed_login_attempts,
                )
                self.db.commit()
                raise AccountLockedError("Account is temporarily locked. Try again later.")
            audit.record_login_failed(
                tenant_id=tenant.id,
                user_id=user.id,
                request=request,
                attempts=user.failed_login_attempts,
            )
            self.db.commit()
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
        audit.record_login_success(tenant_id=tenant.id, user_id=user.id, request=request)
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
        if tenant is None:
            raise ForbiddenError("Tenant is not available")
        assert_tenant_can_authenticate(tenant)

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
        request: Request | None = None,
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

        AuditService(self.db).record_logout(
            tenant_id=claims.tenant_id,
            user_id=claims.sub,
            request=request,
        )
        self.db.commit()

    def validate_access_token(self, token: str) -> AuthenticatedUser:
        """Validate JWT signature, expiry, denylist, and tenant status."""
        try:
            claims = decode_access_token(token, self.settings)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc

        if is_token_denied(claims.jti, self.settings):
            raise UnauthorizedError("Token has been revoked")

        set_rls_tenant_context(self.db, claims.tenant_id)
        tenant_repo = TenantRepository(self.db)
        tenant = tenant_repo.get_by_id(claims.tenant_id)
        if tenant is None:
            raise UnauthorizedError("Invalid tenant context")
        assert_tenant_can_authenticate(tenant)

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

    def forgot_password(self, *, request: Request, email: str) -> str:
        """Issue a password reset token when the user exists; always return generic message."""
        tenant = resolve_tenant_for_login(self.db, request, self.settings)
        set_request_tenant_id(tenant.id)
        set_rls_tenant_context(self.db, tenant.id)

        user_repo = UserRepository(self.db, tenant.id)
        user = user_repo.get_by_email(email)
        if user is not None and user.is_active:
            raw_token = secrets.token_urlsafe(32)
            token_hash = hash_refresh_token(raw_token)
            reset_repo = PasswordResetRepository(self.db, tenant.id)
            reset_repo.invalidate_all_for_user(user.id)
            reset_repo.create_token(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC) + timedelta(hours=PASSWORD_RESET_TOKEN_HOURS),
            )
            self.db.commit()
            self._email.send_password_reset(
                to_email=user.email,
                token=raw_token,
                tenant_id=tenant.id,
                tenant_slug=tenant.slug,
            )

        return FORGOT_PASSWORD_MESSAGE

    def reset_password(
        self,
        *,
        token: str,
        new_password: str,
        request: Request | None = None,
    ) -> str:
        """Consume a one-time reset token, update password, and revoke all sessions."""
        from sqlalchemy import text

        from app.models.core.user import User

        self.db.execute(text("RESET ROLE"))
        token_hash = hash_refresh_token(token)
        reset_row = PasswordResetRepository.find_valid_by_hash(self.db, token_hash)
        if reset_row is None:
            raise UnauthorizedError("Invalid or expired reset token")

        set_rls_tenant_context(self.db, reset_row.tenant_id)
        user = self.db.get(User, reset_row.user_id)
        if (
            user is None
            or user.tenant_id != reset_row.tenant_id
            or user.deleted_at is not None
            or not user.is_active
        ):
            raise UnauthorizedError("Invalid or expired reset token")

        user.password_hash = hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.status == "locked":
            user.status = "active"
        user.updated_by = user.id
        self.db.add(user)

        reset_repo = PasswordResetRepository(self.db, reset_row.tenant_id)
        session_repo = SessionRepository(self.db, reset_row.tenant_id)
        reset_repo.mark_used(reset_row)
        session_repo.revoke_all_for_user(user.id)
        AuditService(self.db).record_password_reset(
            tenant_id=reset_row.tenant_id,
            user_id=user.id,
            request=request,
        )
        self.db.commit()
        return RESET_PASSWORD_SUCCESS_MESSAGE

    def accept_invite(
        self,
        *,
        invite_token: str,
        password: str,
        request: Request,
    ) -> tuple[LoginResponseData, str]:
        """Consume invite token, activate user, and issue login tokens."""
        from sqlalchemy import text

        self.db.execute(text("RESET ROLE"))
        token_hash = hash_refresh_token(invite_token)
        invite_row = UserInviteRepository.find_valid_by_hash(self.db, token_hash)
        if invite_row is None:
            raise UnauthorizedError("Invalid or expired invite token")

        set_rls_tenant_context(self.db, invite_row.tenant_id)
        user = self.db.get(User, invite_row.user_id)
        if (
            user is None
            or user.tenant_id != invite_row.tenant_id
            or user.deleted_at is not None
            or user.status != "inactive"
        ):
            raise UnauthorizedError("Invalid or expired invite token")

        user.password_hash = hash_password(password)
        user.status = "active"
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
        user.updated_by = user.id
        self.db.add(user)

        invite_repo = UserInviteRepository(self.db, invite_row.tenant_id)
        invite_repo.mark_used(invite_row)

        session_repo = SessionRepository(self.db, invite_row.tenant_id)
        session_repo.enforce_session_limit(user.id)

        roles = self._get_user_roles(invite_row.tenant_id, user.id)
        access_token, _jti, expires_in = create_access_token(
            user_id=user.id,
            tenant_id=invite_row.tenant_id,
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
        AuditService(self.db).record_login_success(
            tenant_id=invite_row.tenant_id,
            user_id=user.id,
            request=request,
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

    def verify_email(self, *, token: str) -> str:
        """Consume verification token and set email_verified_at."""
        from sqlalchemy import text

        from app.models.core.user import User

        self.db.execute(text("RESET ROLE"))
        token_hash = hash_refresh_token(token)
        verification_row = EmailVerificationRepository.find_valid_by_hash(self.db, token_hash)
        if verification_row is None:
            raise UnauthorizedError("Invalid or expired verification token")

        set_rls_tenant_context(self.db, verification_row.tenant_id)
        user = self.db.get(User, verification_row.user_id)
        if (
            user is None
            or user.tenant_id != verification_row.tenant_id
            or user.deleted_at is not None
        ):
            raise UnauthorizedError("Invalid or expired verification token")

        verification_repo = EmailVerificationRepository(self.db, verification_row.tenant_id)
        if user.email_verified_at is not None:
            verification_repo.mark_used(verification_row)
            self.db.commit()
            return EMAIL_ALREADY_VERIFIED_MESSAGE

        user.email_verified_at = datetime.now(UTC)
        user.updated_by = user.id
        self.db.add(user)
        verification_repo.mark_used(verification_row)
        self.db.commit()
        return EMAIL_VERIFICATION_SUCCESS_MESSAGE

    def resend_verification(self, *, auth_user: AuthenticatedUser) -> str:
        """Issue a new email verification token for the authenticated user."""
        from app.models.core.user import User

        set_rls_tenant_context(self.db, auth_user.tenant_id)
        user = self.db.get(User, auth_user.user_id)
        if user is None or user.tenant_id != auth_user.tenant_id:
            raise NotFoundError("User not found")
        if user.email_verified_at is not None:
            return EMAIL_ALREADY_VERIFIED_MESSAGE

        self._issue_verification_token(user)
        self.db.commit()
        return RESEND_VERIFICATION_MESSAGE

    def _issue_verification_token(self, user: User) -> None:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_refresh_token(raw_token)
        verification_repo = EmailVerificationRepository(self.db, user.tenant_id)
        verification_repo.invalidate_all_for_user(user.id)
        verification_repo.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_HOURS),
        )
        tenant = TenantRepository(self.db).get_by_id(user.tenant_id)
        tenant_slug = tenant.slug if tenant is not None else ""
        self._email.send_email_verification(
            to_email=user.email,
            token=raw_token,
            tenant_id=user.tenant_id,
            tenant_slug=tenant_slug,
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
