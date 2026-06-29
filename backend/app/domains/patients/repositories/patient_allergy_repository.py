"""core.patient_allergies data access."""

from __future__ import annotations

import uuid

from app.models.core.patient_allergy import PatientAllergy
from app.repositories.base import TenantScopedRepository


class PatientAllergyRepository(TenantScopedRepository):
    def list_by_patient(self, patient_id: uuid.UUID) -> list[PatientAllergy]:
        stmt = (
            self._base_query(PatientAllergy)
            .where(PatientAllergy.patient_id == patient_id)
            .order_by(PatientAllergy.allergen)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_id_for_patient(
        self,
        allergy_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> PatientAllergy | None:
        stmt = self._base_query(PatientAllergy).where(
            PatientAllergy.id == allergy_id,
            PatientAllergy.patient_id == patient_id,
        )
        return self.db.scalars(stmt).first()

    def create(self, *, patient_id: uuid.UUID, **kwargs: object) -> PatientAllergy:
        allergy = PatientAllergy(tenant_id=self.tenant_id, patient_id=patient_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(allergy)
        return allergy
