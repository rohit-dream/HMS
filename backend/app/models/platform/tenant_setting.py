"""platform.tenant_settings — key-value tenant configuration."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class TenantSetting(TenantAuditableEntity):
    """Tenant-scoped configuration (onboarding, clinical, billing defaults)."""

    __tablename__ = "tenant_settings"
    __table_args__ = {"schema": "platform"}

    setting_key: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
