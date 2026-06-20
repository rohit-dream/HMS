"""Tenant location (hospital branch) data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update

from app.models.platform.tenant_location import TenantLocation
from app.repositories.base import TenantScopedRepository


class LocationRepository(TenantScopedRepository):
    def list_active(self) -> list[TenantLocation]:
        stmt = self._base_query(TenantLocation).order_by(
            TenantLocation.is_primary.desc(),
            TenantLocation.name,
        )
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, location_id: uuid.UUID) -> TenantLocation | None:
        return super().get_by_id(TenantLocation, location_id)

    def get_by_code(self, code: str) -> TenantLocation | None:
        stmt = self._base_query(TenantLocation).where(TenantLocation.code == code.upper())
        return self.db.scalars(stmt).first()

    def get_primary(self) -> TenantLocation | None:
        stmt = self._base_query(TenantLocation).where(TenantLocation.is_primary.is_(True))
        return self.db.scalars(stmt).first()

    def count_active(self) -> int:
        stmt = self._base_query(TenantLocation)
        return len(list(self.db.scalars(stmt).all()))

    def create(self, **kwargs: object) -> TenantLocation:
        location = TenantLocation(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(location)
        return location

    def clear_primary_flags(self, *, except_id: uuid.UUID | None = None) -> None:
        stmt = (
            update(TenantLocation)
            .where(
                TenantLocation.tenant_id == self.tenant_id,
                TenantLocation.deleted_at.is_(None),
            )
            .values(is_primary=False)
        )
        if except_id:
            stmt = stmt.where(TenantLocation.id != except_id)
        self.db.execute(stmt)
