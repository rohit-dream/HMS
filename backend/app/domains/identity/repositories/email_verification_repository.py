"""Email verification token data access."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.core.email_verification_token import EmailVerificationToken
from app.repositories.base import TenantScopedRepository


class EmailVerificationRepository(TenantScopedRepository):
    @staticmethod
    def find_valid_by_hash(db: Session, token_hash: str) -> EmailVerificationToken | None:
        """Cross-tenant lookup for public verify-email (token is globally unique)."""
        db.execute(text("RESET ROLE"))
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.deleted_at.is_(None),
            EmailVerificationToken.expires_at > datetime.now(UTC),
        )
        return db.scalars(stmt).first()

    def create_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        created_by: uuid.UUID | None = None,
    ) -> EmailVerificationToken:
        row = EmailVerificationToken(
            tenant_id=self.tenant_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=created_by,
        )
        self.db.add(row)
        return row

    def get_valid_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        stmt = self._base_query(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > datetime.now(UTC),
        )
        return self.db.scalars(stmt).first()

    def get_latest_valid_for_user(self, user_id: uuid.UUID) -> EmailVerificationToken | None:
        stmt = (
            self._base_query(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used_at.is_(None),
                EmailVerificationToken.expires_at > datetime.now(UTC),
            )
            .order_by(EmailVerificationToken.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def mark_used(self, token: EmailVerificationToken) -> None:
        token.used_at = datetime.now(UTC)
        self.db.add(token)

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.tenant_id == self.tenant_id,
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.deleted_at.is_(None),
        )
        now = datetime.now(UTC)
        for row in self.db.scalars(stmt).all():
            row.used_at = now
            self.db.add(row)
