"""
Subdomain/slug → tenant resolution for unauthenticated requests (login).

Per MULTI_TENANT_DESIGN.md:
- Login: tenant from subdomain or slug lookup
- Authenticated API: JWT tenant_id is authoritative
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.constants import TENANT_SLUG_HEADER
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.platform.tenant import Tenant


def extract_subdomain(host: str, base_domain: str) -> str | None:
    """Extract tenant subdomain from Host header (e.g. apollo.platform.com → apollo)."""
    host = host.split(":")[0].lower()
    if host in ("localhost", "127.0.0.1"):
        return None

    base = base_domain.lower()
    if host == base or not host.endswith(f".{base}"):
        return None

    subdomain = host[: -(len(base) + 1)]
    if "." in subdomain:
        return None
    return subdomain or None


def resolve_tenant_for_login(
    db: Session,
    request: Request,
    settings: Settings | None = None,
) -> Tenant:
    """
    Resolve tenant for login/register from Host subdomain or X-Tenant-Slug (dev).

    Raises NotFoundError if tenant not found.
    Raises ForbiddenError if tenant blocked from login.
    """
    settings = settings or get_settings()
    slug_or_subdomain: str | None = None

    tenant_slug_header = request.headers.get(TENANT_SLUG_HEADER)
    if tenant_slug_header:
        slug_or_subdomain = tenant_slug_header.strip().lower()
    else:
        host = request.headers.get("host", "")
        slug_or_subdomain = extract_subdomain(host, settings.tenant_base_domain)

    if not slug_or_subdomain:
        raise NotFoundError(
            "Tenant could not be resolved. Use subdomain or X-Tenant-Slug header.",
            field="tenant",
        )

    stmt = (
        select(Tenant)
        .where(Tenant.deleted_at.is_(None))
        .where((Tenant.subdomain == slug_or_subdomain) | (Tenant.slug == slug_or_subdomain))
    )
    tenant = db.scalars(stmt).first()
    if tenant is None:
        raise NotFoundError("Tenant not found", field="tenant")

    if not tenant.is_login_allowed:
        raise ForbiddenError(
            "Tenant is not available for login",
            field="tenant",
        )

    return tenant
