"""OPD clinical notes."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.clinical.repositories.opd_clinical_note_repository import OpdClinicalNoteRepository
from app.domains.clinical.repositories.opd_visit_repository import OpdVisitRepository
from app.domains.clinical.schemas.opd.notes import OpdClinicalNoteResponse, OpdNoteCreateRequest
from app.models.clinical.opd import OpdClinicalNote

VALID_NOTE_TYPES = frozenset({"examination", "diagnosis", "plan", "general"})
TERMINAL_VISIT_STATUSES = frozenset({"completed", "cancelled"})


class OpdClinicalNoteService:
    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = OpdClinicalNoteRepository(db, tenant_id)
        self._visit_repo = OpdVisitRepository(db, tenant_id)

    def create_note(
        self,
        visit_id: uuid.UUID,
        payload: OpdNoteCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdClinicalNoteResponse:
        visit = self._visit_repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status in TERMINAL_VISIT_STATUSES:
            raise ConflictError(
                "Cannot add notes to a completed or cancelled visit",
                field="status",
            )
        if payload.note_type not in VALID_NOTE_TYPES:
            raise ValidationError("Invalid note type", field="note_type")

        note = self._repo.create(
            opd_visit_id=visit_id,
            note_type=payload.note_type,
            content=payload.content,
            icd_code=payload.icd_code,
            icd_description=payload.icd_description,
            is_final=False,
            created_by=actor_id,
        )
        self.db.flush()
        response = self._response_from(note)
        self.db.commit()
        return response

    def list_notes(
        self,
        visit_id: uuid.UUID,
        *,
        note_type: str | None = None,
    ) -> list[OpdClinicalNoteResponse]:
        if note_type is not None and note_type not in VALID_NOTE_TYPES:
            raise ValidationError("Invalid note type", field="note_type")
        if self._visit_repo.get_by_id(visit_id) is None:
            raise NotFoundError("OPD visit not found", field="visit_id")

        rows = self._repo.list_for_visit(visit_id, note_type=note_type)
        responses = [self._response_from(row) for row in rows]
        self.db.commit()
        return responses

    def _response_from(self, note: OpdClinicalNote) -> OpdClinicalNoteResponse:
        return OpdClinicalNoteResponse(
            id=note.id,
            opd_visit_id=note.opd_visit_id,
            note_type=note.note_type,  # type: ignore[arg-type]
            content=note.content,
            icd_code=note.icd_code,
            icd_description=note.icd_description,
            is_final=note.is_final,
            created_by_user_id=note.created_by,
            created_at=note.created_at,
        )
