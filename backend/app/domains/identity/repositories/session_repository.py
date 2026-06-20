"""Refresh token session data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.constants import MAX_SESSIONS_PER_USER
from app.models.core.user_session import UserSession
from app.repositories.base import TenantScopedRepository


class SessionRepository(TenantScopedRepository):
    def create_session(
        self,
        *,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserSession:
        session = UserSession(
            tenant_id=self.tenant_id,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(session)
        return session

    def get_active_by_token_hash(self, token_hash: str) -> UserSession | None:
        stmt = (
            select(UserSession)
            .where(
                UserSession.tenant_id == self.tenant_id,
                UserSession.refresh_token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.deleted_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )
        return self.db.scalars(stmt).first()

    def get_revoked_by_token_hash(self, token_hash: str) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.revoked_at.isnot(None),
        )
        return self.db.scalars(stmt).first()

    def revoke_session(self, session: UserSession) -> None:
        session.revoked_at = datetime.now(UTC)
        self.db.add(session)

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(UserSession).where(
            UserSession.tenant_id == self.tenant_id,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.deleted_at.is_(None),
        )
        sessions = list(self.db.scalars(stmt).all())
        now = datetime.now(UTC)
        for session in sessions:
            session.revoked_at = now
            self.db.add(session)
        return len(sessions)

    def enforce_session_limit(self, user_id: uuid.UUID) -> None:
        stmt = (
            select(UserSession)
            .where(
                UserSession.tenant_id == self.tenant_id,
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.deleted_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
            .order_by(UserSession.created_at.asc())
        )
        active = list(self.db.scalars(stmt).all())
        overflow = len(active) - MAX_SESSIONS_PER_USER + 1
        if overflow > 0:
            for session in active[:overflow]:
                self.revoke_session(session)
