"""core.permissions — permission catalog per tenant."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class Permission(TenantAuditableEntity):
    """Atomic permission (module:action) seeded from system tenant."""

    __tablename__ = "permissions"
    __table_args__ = {"schema": "core"}

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
