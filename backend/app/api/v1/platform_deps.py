"""Platform and hospital API dependencies."""

from __future__ import annotations

import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.platform.services.hospital_service import HospitalService
from app.domains.platform.services.tenant_service import TenantService


def get_tenant_service(db: Session = Depends(get_db)) -> TenantService:
    return TenantService(db)


def get_hospital_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> HospitalService:
    """Hospital service bound to authenticated user's tenant (JWT authoritative)."""
    return HospitalService(db, ctx.user.tenant_id)


def get_platform_tenant_id(tenant_id: uuid.UUID) -> uuid.UUID:
    """Path param extractor for platform-admin routes."""
    return tenant_id
