"""core.patient_contacts data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update

from app.models.core.patient_contact import PatientContact
from app.repositories.base import TenantScopedRepository


class PatientContactRepository(TenantScopedRepository):
    def list_by_patient(self, patient_id: uuid.UUID) -> list[PatientContact]:
        stmt = (
            self._base_query(PatientContact)
            .where(PatientContact.patient_id == patient_id)
            .order_by(PatientContact.is_primary.desc(), PatientContact.name)
        )
        return list(self.db.scalars(stmt).all())

    def create(self, *, patient_id: uuid.UUID, **kwargs: object) -> PatientContact:
        contact = PatientContact(tenant_id=self.tenant_id, patient_id=patient_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(contact)
        return contact

    def clear_primary_for_patient(self, patient_id: uuid.UUID) -> None:
        stmt = (
            update(PatientContact)
            .where(
                PatientContact.tenant_id == self.tenant_id,
                PatientContact.patient_id == patient_id,
                PatientContact.deleted_at.is_(None),
                PatientContact.is_primary.is_(True),
            )
            .values(is_primary=False)
        )
        self.db.execute(stmt)
