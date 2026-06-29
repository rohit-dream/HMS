"""Appointment API dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.clinical.services.appointment_service import AppointmentService


def get_appointment_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> AppointmentService:
    return AppointmentService(db, ctx.user.tenant_id)
