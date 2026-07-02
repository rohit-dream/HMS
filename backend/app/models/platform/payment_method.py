"""platform.payment_methods — tokenized SaaS payment methods."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantAuditableEntity


class PaymentMethod(TenantAuditableEntity):
    __tablename__ = "payment_methods"
    __table_args__ = {"schema": "platform"}

    gateway: Mapped[str] = mapped_column(String(20), nullable=False, default="razorpay")
    gateway_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    gateway_token_id: Mapped[str] = mapped_column(String(255), nullable=False)
    method_type: Mapped[str] = mapped_column(String(20), nullable=False)
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
