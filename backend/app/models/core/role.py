"""core.roles — tenant-scoped RBAC roles."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class Role(TenantAuditableEntity):
    """Role definition cloned per tenant from system templates."""

    __tablename__ = "roles"
    __table_args__ = {"schema": "core"}

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
