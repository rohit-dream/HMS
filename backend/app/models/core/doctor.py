"""core.doctors — doctor profiles extending staff."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class Doctor(TenantAuditableEntity):
    __tablename__ = "doctors"
    __table_args__ = {"schema": "core"}

    staff_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    specialization: Mapped[str] = mapped_column(String(150), nullable=False)
    qualification: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    follow_up_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
