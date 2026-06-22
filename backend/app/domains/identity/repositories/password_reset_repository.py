"""Password reset token data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.core.password_reset_token import PasswordResetToken
from app.repositories.base import TenantScopedRepository


class PasswordResetRepository(TenantScopedRepository):
    def create_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        created_by: uuid.UUID | None = None,
    ) -> PasswordResetToken:
        row = PasswordResetToken(
            tenant_id=self.tenant_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=created_by,
        )
        self.db.add(row)
        return row

    def get_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = self._base_query(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(UTC),
        )
        return self.db.scalars(stmt).first()

    def mark_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(UTC)
        self.db.add(token)

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.tenant_id == self.tenant_id,
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.deleted_at.is_(None),
        )
        now = datetime.now(UTC)
        for row in self.db.scalars(stmt).all():
            row.used_at = now
            self.db.add(row)
