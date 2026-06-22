"""Per-request tenant context from JWT (authoritative) or login resolution."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from contextvars import ContextVar

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_tenant_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("auth_tenant_id", default=None)
_user_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("auth_user_id", default=None)
_rls_tenant_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("rls_tenant_id", default=None)


def set_auth_context(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    _tenant_id_ctx.set(tenant_id)
    _user_id_ctx.set(user_id)
    _rls_tenant_id_ctx.set(tenant_id)


def set_request_tenant_id(tenant_id: uuid.UUID) -> None:
    """Bind tenant for pre-auth flows (login) and background jobs."""
    _rls_tenant_id_ctx.set(tenant_id)


def get_current_tenant_id() -> uuid.UUID | None:
    return _tenant_id_ctx.get()


def get_current_user_id() -> uuid.UUID | None:
    return _user_id_ctx.get()


def get_effective_tenant_id() -> uuid.UUID | None:
    """JWT tenant (if set) or explicit request/job tenant for RLS."""
    return _tenant_id_ctx.get() or _rls_tenant_id_ctx.get()


def clear_auth_context() -> None:
    _tenant_id_ctx.set(None)
    _user_id_ctx.set(None)
    _rls_tenant_id_ctx.set(None)


@contextmanager
def tenant_db_session(db: Session, tenant_id: uuid.UUID) -> Generator[Session, None, None]:
    """
    Scope all DB operations in the block to a tenant (RLS + context var).

    Use in scripts, tests, and workers when no JWT is available.
    """
    from app.core.database import set_rls_tenant_context

    token = _rls_tenant_id_ctx.set(tenant_id)
    set_rls_tenant_context(db, tenant_id)
    try:
        yield db
    finally:
        _rls_tenant_id_ctx.reset(token)
        set_rls_tenant_context(db, None)
