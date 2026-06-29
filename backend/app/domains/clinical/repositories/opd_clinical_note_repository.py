"""clinical.opd_clinical_notes data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.clinical.opd import OpdClinicalNote
from app.repositories.base import TenantScopedRepository


class OpdClinicalNoteRepository(TenantScopedRepository):
    def get_by_id(self, note_id: uuid.UUID) -> OpdClinicalNote | None:
        return super().get_by_id(OpdClinicalNote, note_id)

    def list_for_visit(
        self,
        visit_id: uuid.UUID,
        *,
        note_type: str | None = None,
    ) -> list[OpdClinicalNote]:
        stmt = self._base_query(OpdClinicalNote).where(OpdClinicalNote.opd_visit_id == visit_id)
        if note_type is not None:
            stmt = stmt.where(OpdClinicalNote.note_type == note_type)
        stmt = stmt.order_by(OpdClinicalNote.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def create(self, **kwargs: object) -> OpdClinicalNote:
        note = OpdClinicalNote(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(note)
        return note
