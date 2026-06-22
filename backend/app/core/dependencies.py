"""Shared FastAPI dependencies — Sprint 2 expands with auth."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.v1.auth_deps import get_current_user
from app.core.database import get_db
from app.domains.identity.services.auth_service import AuthenticatedUser


def get_tenant_db(
    db: Annotated[Session, Depends(get_db)],
    _auth_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> Session:
    """
    Authenticated database session with JWT tenant bound for RLS.

    Depends on get_current_user so `app.tenant_id` is set before handlers run.
    """
    return db
