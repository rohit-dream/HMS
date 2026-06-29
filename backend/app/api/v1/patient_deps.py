"""Patient API dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.patients.services.patient_service import PatientService


def get_patient_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> PatientService:
    return PatientService(db, ctx.user.tenant_id)
