"""Per-request tenant context from JWT (authoritative) or login resolution."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_tenant_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("auth_tenant_id", default=None)
_user_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("auth_user_id", default=None)


def set_auth_context(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    _tenant_id_ctx.set(tenant_id)
    _user_id_ctx.set(user_id)


def get_current_tenant_id() -> uuid.UUID | None:
    return _tenant_id_ctx.get()


def get_current_user_id() -> uuid.UUID | None:
    return _user_id_ctx.get()


def clear_auth_context() -> None:
    _tenant_id_ctx.set(None)
    _user_id_ctx.set(None)
