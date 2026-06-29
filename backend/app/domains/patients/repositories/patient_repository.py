"""core.patients data access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select, text

from app.models.core.patient import Patient
from app.repositories.base import TenantScopedRepository


class PatientRepository(TenantScopedRepository):
    def get_by_id(self, patient_id: uuid.UUID) -> Patient | None:
        return super().get_by_id(Patient, patient_id)

    def generate_mrn(self) -> str:
        self.apply_rls_context()
        return self.db.execute(
            text("SELECT core.generate_mrn(:tenant_id)"),
            {"tenant_id": self.tenant_id},
        ).scalar_one()

    def get_by_phone(self, phone: str, *, exclude_id: uuid.UUID | None = None) -> Patient | None:
        stmt = self._base_query(Patient).where(Patient.phone == phone)
        if exclude_id is not None:
            stmt = stmt.where(Patient.id != exclude_id)
        return self.db.scalars(stmt).first()

    def create(self, **kwargs: object) -> Patient:
        patient = Patient(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(patient)
        return patient

    def search(
        self,
        *,
        query: str | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Patient], int]:
        stmt = self._base_query(Patient)
        count_stmt = select(func.count()).select_from(Patient).where(
            Patient.tenant_id == self.tenant_id,
            Patient.deleted_at.is_(None),
        )

        if location_id is not None:
            stmt = stmt.where(Patient.location_id == location_id)
            count_stmt = count_stmt.where(Patient.location_id == location_id)

        if query:
            trimmed = query.strip()
            pattern = f"%{trimmed}%"
            name_trgm = text(
                "(first_name || ' ' || COALESCE(last_name, '')) % :trgm_query"
            ).bindparams(trgm_query=trimmed)
            criterion = or_(
                name_trgm,
                Patient.phone.ilike(pattern),
                Patient.mrn.ilike(pattern),
                Patient.email.ilike(pattern),
            )
            stmt = stmt.where(criterion)
            count_stmt = count_stmt.where(criterion)

        total = self.db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = (
            stmt.order_by(Patient.last_name.nulls_last(), Patient.first_name)
            .offset(offset)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), int(total)

    def find_potential_duplicates(
        self,
        *,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        exclude_id: uuid.UUID | None = None,
        limit: int = 10,
    ) -> list[tuple[Patient, list[str]]]:
        """Return patients matching phone and/or fuzzy name with match reason tags."""
        found: dict[uuid.UUID, tuple[Patient, list[str]]] = {}

        def _add(patient: Patient, reason: str) -> None:
            if exclude_id is not None and patient.id == exclude_id:
                return
            if patient.id in found:
                reasons = found[patient.id][1]
                if reason not in reasons:
                    reasons.append(reason)
                return
            found[patient.id] = (patient, [reason])

        if phone:
            match = self.get_by_phone(phone, exclude_id=exclude_id)
            if match is not None:
                _add(match, "phone")

        if first_name and len(first_name.strip()) >= 2:
            full_name = f"{first_name.strip()} {last_name.strip() if last_name else ''}".strip()
            name_stmt = (
                self._base_query(Patient)
                .where(
                    text("(first_name || ' ' || COALESCE(last_name, '')) % :trgm_query").bindparams(
                        trgm_query=full_name
                    )
                )
                .limit(limit)
            )
            if exclude_id is not None:
                name_stmt = name_stmt.where(Patient.id != exclude_id)
            for patient in self.db.scalars(name_stmt).all():
                _add(patient, "name")

        return list(found.values())[:limit]

    def count_active(self) -> int:
        """Count non-deleted patients for the current tenant."""
        stmt = select(func.count()).select_from(Patient).where(
            Patient.tenant_id == self.tenant_id,
            Patient.deleted_at.is_(None),
        )
        return int(self.db.scalar(stmt) or 0)
