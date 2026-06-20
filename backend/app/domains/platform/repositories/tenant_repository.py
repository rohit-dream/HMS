"""Platform tenant data access — cross-tenant registry operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.platform.tenant import Tenant


class TenantRepository:
    """Platform-level tenant registry (not tenant-scoped)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        stmt = select(Tenant).where(
            Tenant.id == tenant_id,
            Tenant.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first()

    def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(
            Tenant.slug == slug.lower(),
            Tenant.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first()

    def get_by_subdomain(self, subdomain: str) -> Tenant | None:
        stmt = select(Tenant).where(
            Tenant.subdomain == subdomain.lower(),
            Tenant.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first()

    def slug_exists(self, slug: str) -> bool:
        return self.get_by_slug(slug) is not None

    def subdomain_exists(self, subdomain: str) -> bool:
        return self.get_by_subdomain(subdomain) is not None

    def create_via_db_function(
        self,
        *,
        name: str,
        slug: str,
        email: str,
        subdomain: str | None = None,
        country: str = "IN",
        timezone: str = "Asia/Kolkata",
        currency: str = "INR",
    ) -> uuid.UUID:
        """Create tenant root via platform.create_tenant() — id = tenant_id."""
        result = self.db.execute(
            text(
                """
                SELECT platform.create_tenant(
                    :name, :slug, :email, :subdomain, :country, :timezone, :currency
                )
                """
            ),
            {
                "name": name,
                "slug": slug,
                "email": str(email).lower(),
                "subdomain": subdomain or slug,
                "country": country,
                "timezone": timezone,
                "currency": currency,
            },
        )
        tenant_id = result.scalar_one()
        return uuid.UUID(str(tenant_id))

    def update_status(self, tenant: Tenant, status: str, *, updated_by: uuid.UUID | None = None) -> Tenant:
        tenant.status = status
        tenant.updated_by = updated_by
        self.db.add(tenant)
        return tenant

    def update_profile(
        self,
        tenant: Tenant,
        *,
        updated_by: uuid.UUID | None = None,
        **fields: object,
    ) -> Tenant:
        for key, value in fields.items():
            if value is not None and hasattr(tenant, key):
                setattr(tenant, key, value)
        tenant.updated_by = updated_by
        self.db.add(tenant)
        return tenant
