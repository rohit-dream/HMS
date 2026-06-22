"""core.password_reset_tokens — password reset workflow."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class PasswordResetToken(TenantAuditableEntity):
    """One-time password reset token (hashed at rest)."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = {"schema": "core"}

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_valid(self) -> bool:
        from datetime import UTC

        return self.used_at is None and self.deleted_at is None and self.expires_at > datetime.now(UTC)
