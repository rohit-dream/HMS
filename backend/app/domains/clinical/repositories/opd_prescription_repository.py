"""clinical.opd_prescriptions data access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select, text

from app.models.clinical.opd import OpdPrescription, OpdPrescriptionItem
from app.repositories.base import TenantScopedRepository


@dataclass(frozen=True)
class OpdPrescriptionWithItems:
    prescription: OpdPrescription
    items: list[OpdPrescriptionItem]


class OpdPrescriptionRepository(TenantScopedRepository):
    def generate_prescription_number(self) -> str:
        return self.db.execute(
            text("SELECT clinical.generate_prescription_number(:tenant_id)"),
            {"tenant_id": self.tenant_id},
        ).scalar_one()

    def get_by_id(self, prescription_id: uuid.UUID) -> OpdPrescription | None:
        return super().get_by_id(OpdPrescription, prescription_id)

    def get_with_items(self, prescription_id: uuid.UUID) -> OpdPrescriptionWithItems | None:
        prescription = self.get_by_id(prescription_id)
        if prescription is None:
            return None
        items = self.list_items(prescription_id)
        return OpdPrescriptionWithItems(prescription=prescription, items=items)

    def list_items(self, prescription_id: uuid.UUID) -> list[OpdPrescriptionItem]:
        stmt = (
            self._base_query(OpdPrescriptionItem)
            .where(OpdPrescriptionItem.prescription_id == prescription_id)
            .order_by(OpdPrescriptionItem.created_at)
        )
        return list(self.db.scalars(stmt).all())

    def list_for_visit(self, visit_id: uuid.UUID) -> list[OpdPrescriptionWithItems]:
        stmt = (
            self._base_query(OpdPrescription)
            .where(OpdPrescription.opd_visit_id == visit_id)
            .order_by(OpdPrescription.prescribed_at.desc())
        )
        prescriptions = list(self.db.scalars(stmt).all())
        return [
            OpdPrescriptionWithItems(prescription=rx, items=self.list_items(rx.id))
            for rx in prescriptions
        ]

    def create_prescription(self, **kwargs: object) -> OpdPrescription:
        prescription = OpdPrescription(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(prescription)
        return prescription

    def create_item(self, **kwargs: object) -> OpdPrescriptionItem:
        item = OpdPrescriptionItem(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(item)
        return item
