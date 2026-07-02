"""Subscription API dependencies (tenant-scoped SaaS billing)."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.platform.services.payment_method_service import PaymentMethodService


def get_payment_method_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> PaymentMethodService:
    return PaymentMethodService(db, ctx.user.tenant_id)

