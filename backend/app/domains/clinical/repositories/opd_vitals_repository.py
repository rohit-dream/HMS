"""clinical.opd_vitals data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.clinical.opd import OpdVitals
from app.repositories.base import TenantScopedRepository


class OpdVitalsRepository(TenantScopedRepository):
    def get_by_id(self, vitals_id: uuid.UUID) -> OpdVitals | None:
        return super().get_by_id(OpdVitals, vitals_id)

    def list_for_visit(self, visit_id: uuid.UUID) -> list[OpdVitals]:
        stmt = (
            self._base_query(OpdVitals)
            .where(OpdVitals.opd_visit_id == visit_id)
            .order_by(OpdVitals.recorded_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_for_visit(self, visit_id: uuid.UUID) -> OpdVitals | None:
        stmt = (
            self._base_query(OpdVitals)
            .where(OpdVitals.opd_visit_id == visit_id)
            .order_by(OpdVitals.recorded_at.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def create(self, **kwargs: object) -> OpdVitals:
        vitals = OpdVitals(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(vitals)
        return vitals
