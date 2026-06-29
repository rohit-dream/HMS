"""OPD API dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.clinical.services.opd_clinical_note_service import OpdClinicalNoteService
from app.domains.clinical.services.opd_prescription_service import OpdPrescriptionService
from app.domains.clinical.services.opd_queue_service import OpdQueueService
from app.domains.clinical.services.opd_visit_service import OpdVisitService
from app.domains.clinical.services.opd_vitals_service import OpdVitalsService


def get_opd_visit_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> OpdVisitService:
    return OpdVisitService(db, ctx.user.tenant_id)


def get_opd_queue_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> OpdQueueService:
    return OpdQueueService(db, ctx.user.tenant_id)


def get_opd_vitals_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> OpdVitalsService:
    return OpdVitalsService(db, ctx.user.tenant_id)


def get_opd_clinical_note_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> OpdClinicalNoteService:
    return OpdClinicalNoteService(db, ctx.user.tenant_id)


def get_opd_prescription_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> OpdPrescriptionService:
    return OpdPrescriptionService(db, ctx.user.tenant_id)
