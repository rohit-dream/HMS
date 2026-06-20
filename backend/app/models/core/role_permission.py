"""core.role_permissions — role-to-permission junction."""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class RolePermission(TenantAuditableEntity):
    """Maps a role to a permission within a tenant."""

    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "core"}

    role_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
