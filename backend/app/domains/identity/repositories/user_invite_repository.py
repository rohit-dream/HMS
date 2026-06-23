"""User invite token data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.core.user_invite_token import UserInviteToken
from app.repositories.base import TenantScopedRepository


class UserInviteRepository(TenantScopedRepository):
    @staticmethod
    def find_valid_by_hash(db: Session, token_hash: str) -> UserInviteToken | None:
        """Cross-tenant lookup for public accept-invite (token is globally unique)."""
        db.execute(text("RESET ROLE"))
        stmt = select(UserInviteToken).where(
            UserInviteToken.token_hash == token_hash,
            UserInviteToken.used_at.is_(None),
            UserInviteToken.deleted_at.is_(None),
            UserInviteToken.expires_at > datetime.now(UTC),
        )
        return db.scalars(stmt).first()

    def create_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        created_by: uuid.UUID | None = None,
    ) -> UserInviteToken:
        row = UserInviteToken(
            tenant_id=self.tenant_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=created_by,
        )
        self.db.add(row)
        return row

    def get_valid_by_hash(self, token_hash: str) -> UserInviteToken | None:
        stmt = self._base_query(UserInviteToken).where(
            UserInviteToken.token_hash == token_hash,
            UserInviteToken.used_at.is_(None),
            UserInviteToken.expires_at > datetime.now(UTC),
        )
        return self.db.scalars(stmt).first()

    def mark_used(self, token: UserInviteToken) -> None:
        token.used_at = datetime.now(UTC)
        self.db.add(token)

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = select(UserInviteToken).where(
            UserInviteToken.tenant_id == self.tenant_id,
            UserInviteToken.user_id == user_id,
            UserInviteToken.used_at.is_(None),
            UserInviteToken.deleted_at.is_(None),
        )
        now = datetime.now(UTC)
        for row in self.db.scalars(stmt).all():
            row.used_at = now
            self.db.add(row)
