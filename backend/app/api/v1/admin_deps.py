"""Admin API dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.identity.services.user_management_service import UserManagementService


def get_user_management_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> UserManagementService:
    return UserManagementService(db, ctx.user.tenant_id)
