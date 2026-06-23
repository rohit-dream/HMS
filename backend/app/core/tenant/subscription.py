"""Tenant subscription status policy — trial/active/past_due/suspended/cancelled."""

from __future__ import annotations

from starlette.requests import Request

from app.core.exceptions import ForbiddenError, TenantSuspendedError
from app.models.platform.tenant import Tenant

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Auth/session endpoints that stay writable during past_due grace read-only mode.
PAST_DUE_MUTATION_EXEMPT_PATHS = frozenset({
    "/auth/logout",
    "/auth/refresh",
})


def _relative_api_path(path: str, api_v1_prefix: str) -> str:
    prefix = api_v1_prefix.rstrip("/")
    if path.startswith(prefix):
        return path[len(prefix) :] or "/"
    return path


def is_past_due_mutation_exempt(path: str, api_v1_prefix: str) -> bool:
    relative = _relative_api_path(path, api_v1_prefix)
    return relative in PAST_DUE_MUTATION_EXEMPT_PATHS


def assert_tenant_can_authenticate(tenant: Tenant) -> None:
    """Block JWT use for suspended or cancelled tenants."""
    if tenant.deleted_at is not None:
        raise TenantSuspendedError("Tenant is not available")
    if tenant.status == "suspended":
        raise TenantSuspendedError("Tenant is suspended")
    if tenant.status == "cancelled":
        raise TenantSuspendedError("Tenant subscription is cancelled")


def enforce_tenant_subscription(
    request: Request,
    tenant: Tenant,
    *,
    api_v1_prefix: str,
) -> None:
    """
    Enforce subscription gates on authenticated requests.

    - trial / active: full access
    - past_due: read-only (mutations blocked except auth/session exempt paths)
    - suspended / cancelled: blocked at token validation
    """
    assert_tenant_can_authenticate(tenant)

    if tenant.status != "past_due":
        return

    if request.method not in MUTATING_METHODS:
        return

    if is_past_due_mutation_exempt(request.url.path, api_v1_prefix):
        return

    raise ForbiddenError(
        "Subscription payment is overdue — account is read-only until billing is updated",
        field="subscription",
    )
