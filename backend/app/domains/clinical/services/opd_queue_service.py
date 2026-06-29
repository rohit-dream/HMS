"""Tenant-scoped OPD queue operations."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.clinical.queue_poll import compute_queue_etag
from app.domains.clinical.repositories.opd_queue_repository import (
    OpdQueueEntryWithDetails,
    OpdQueueRepository,
)
from app.domains.clinical.repositories.opd_visit_repository import OpdVisitRepository
from app.domains.clinical.schemas.opd.queue import (
    OpdQueueBoardResponse,
    OpdQueueCreateRequest,
    OpdQueueEntryResponse,
    OpdQueuePollResponse,
    OpdQueueSkipRequest,
    OpdQueueUpdateRequest,
)
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.models.clinical.opd import OpdQueue


class OpdQueueService:
    """OPD queue board — scoped to JWT tenant_id."""

    BOARD_FILTER_STATUSES = frozenset({"waiting", "called", "in_consultation"})

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = OpdQueueRepository(db, tenant_id)
        self._visit_repo = OpdVisitRepository(db, tenant_id)
        self._doctor_repo = DoctorRepository(db, tenant_id)

    def get_queue_board(
        self,
        *,
        doctor_id: uuid.UUID,
        queue_date: date | None = None,
        location_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> OpdQueueBoardResponse:
        if self._doctor_repo.get_by_id(doctor_id) is None:
            raise NotFoundError("Doctor not found", field="doctor_id")
        if status is not None and status not in self.BOARD_FILTER_STATUSES:
            raise ValidationError("Invalid queue status filter", field="status")

        target_date = queue_date or date.today()
        entries = self._repo.list_board_entries(
            doctor_id=doctor_id,
            queue_date=target_date,
            location_id=location_id,
            status=status,
        )

        current_token = self._resolve_current_token(entries)
        waiting_count = sum(1 for row in entries if row.queue.status == "waiting")

        response = OpdQueueBoardResponse(
            doctor_id=doctor_id,
            queue_date=target_date,
            current_token=current_token,
            waiting_count=waiting_count,
            entries=[self._entry_response(row) for row in entries],
        )
        self.db.commit()
        return response

    def poll_queue_board(
        self,
        *,
        doctor_id: uuid.UUID,
        queue_date: date | None = None,
        location_id: uuid.UUID | None = None,
        status: str | None = None,
        if_none_match: str | None = None,
    ) -> tuple[OpdQueuePollResponse | None, str]:
        """Return queue poll payload and ETag; None data when client etag matches."""
        board = self.get_queue_board(
            doctor_id=doctor_id,
            queue_date=queue_date,
            location_id=location_id,
            status=status,
        )
        etag = compute_queue_etag(board)
        client_etag = _normalize_etag(if_none_match)
        if client_etag is not None and client_etag == etag:
            return None, etag

        return (
            OpdQueuePollResponse(
                **board.model_dump(),
                etag=etag,
                poll_interval_seconds=5,
                changed=True,
            ),
            etag,
        )

    def add_to_queue(
        self,
        payload: OpdQueueCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdQueueEntryResponse:
        visit = self._visit_repo.get_by_id(payload.opd_visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="opd_visit_id")
        if visit.status in ("completed", "cancelled"):
            raise ConflictError(
                "Cannot queue a completed or cancelled visit",
                field="opd_visit_id",
            )
        if self._repo.get_active_for_visit(visit.id) is not None:
            raise ConflictError(
                "Visit is already in the active queue",
                field="opd_visit_id",
            )

        token_number = self._repo.next_token_number(
            doctor_id=visit.doctor_id,
            queue_date=visit.visit_date,
        )
        entry = self._repo.create(
            opd_visit_id=visit.id,
            doctor_id=visit.doctor_id,
            token_number=token_number,
            queue_date=visit.visit_date,
            status="waiting",
            priority=payload.priority,
            created_by=actor_id,
        )
        visit.token_number = token_number
        visit.updated_by = actor_id
        self.db.add(visit)

        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "Visit is already in the active queue",
                field="opd_visit_id",
            ) from exc

        row = self._repo.get_with_details(entry.id)
        assert row is not None
        response = self._entry_response(row)
        self.db.commit()
        return response

    def update_queue_entry(
        self,
        queue_id: uuid.UUID,
        payload: OpdQueueUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdQueueEntryResponse:
        row = self._repo.get_with_details(queue_id)
        if row is None:
            raise NotFoundError("Queue entry not found", field="queue_id")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        entry = row.queue
        if "priority" in update_data:
            entry.priority = update_data["priority"]
            entry.updated_by = actor_id
            self.db.add(entry)

        if "position" in update_data:
            if entry.status != "waiting":
                raise ConflictError(
                    "Only waiting queue entries can be reordered",
                    field="status",
                )
            self._reorder_waiting_entry(
                entry,
                target_position=update_data["position"],
                actor_id=actor_id,
            )

        self.db.flush()
        updated = self._repo.get_with_details(queue_id)
        assert updated is not None
        response = self._entry_response(updated)
        self.db.commit()
        return response

    def call_patient(
        self,
        queue_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdQueueEntryResponse:
        row = self._require_queue_entry(queue_id)
        entry = row.queue
        if entry.status != "waiting":
            raise ConflictError(
                "Only waiting patients can be called",
                field="status",
            )

        now = datetime.now(UTC)
        entry.status = "called"
        entry.called_at = now
        entry.updated_by = actor_id
        self.db.add(entry)
        self.db.flush()

        updated = self._repo.get_with_details(queue_id)
        assert updated is not None
        response = self._entry_response(updated)
        self.db.commit()
        return response

    def complete_queue_entry(
        self,
        queue_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdQueueEntryResponse:
        row = self._require_queue_entry(queue_id)
        entry = row.queue
        if entry.status in ("completed", "skipped"):
            raise ConflictError(
                f"Queue entry is already {entry.status}",
                field="status",
            )

        entry.status = "completed"
        entry.updated_by = actor_id
        self.db.add(entry)
        self.db.flush()

        updated = self._repo.get_with_details(queue_id)
        assert updated is not None
        response = self._entry_response(updated)
        self.db.commit()
        return response

    def skip_patient(
        self,
        queue_id: uuid.UUID,
        payload: OpdQueueSkipRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdQueueEntryResponse:
        _ = payload
        row = self._require_queue_entry(queue_id)
        entry = row.queue
        if entry.status in ("completed", "skipped"):
            raise ConflictError(
                f"Queue entry is already {entry.status}",
                field="status",
            )

        doctor_id = entry.doctor_id
        queue_date = entry.queue_date
        entry.status = "skipped"
        entry.updated_by = actor_id
        self.db.add(entry)
        self.db.flush()

        waiting = self._repo.list_waiting_entries(doctor_id=doctor_id, queue_date=queue_date)
        self._repo.reassign_waiting_token_numbers(waiting, actor_id=actor_id)
        self.db.flush()

        updated = self._repo.get_with_details(queue_id)
        assert updated is not None
        response = self._entry_response(updated)
        self.db.commit()
        return response

    def _require_queue_entry(self, queue_id: uuid.UUID) -> OpdQueueEntryWithDetails:
        row = self._repo.get_with_details(queue_id)
        if row is None:
            raise NotFoundError("Queue entry not found", field="queue_id")
        return row

    def _reorder_waiting_entry(
        self,
        entry: OpdQueue,
        *,
        target_position: int,
        actor_id: uuid.UUID | None,
    ) -> None:
        waiting = self._repo.list_waiting_entries(
            doctor_id=entry.doctor_id,
            queue_date=entry.queue_date,
        )
        if not waiting:
            return

        ordered = list(waiting)
        try:
            current_index = next(i for i, item in enumerate(ordered) if item.id == entry.id)
        except StopIteration as exc:
            raise NotFoundError("Queue entry not found", field="queue_id") from exc

        ordered.pop(current_index)
        insert_at = min(max(target_position - 1, 0), len(ordered))
        ordered.insert(insert_at, entry)
        self._repo.reassign_waiting_token_numbers(ordered, actor_id=actor_id)

        for item in ordered:
            visit = self._visit_repo.get_by_id(item.opd_visit_id)
            if visit is not None:
                visit.token_number = item.token_number
                visit.updated_by = actor_id
                self.db.add(visit)

    def _resolve_current_token(self, entries: list[OpdQueueEntryWithDetails]) -> int | None:
        in_consultation = [
            row.queue.token_number
            for row in entries
            if row.queue.status == "in_consultation"
        ]
        if in_consultation:
            return max(in_consultation)

        called = [
            row
            for row in entries
            if row.queue.status == "called" and row.queue.called_at is not None
        ]
        if called:
            latest = max(called, key=lambda row: row.queue.called_at)  # type: ignore[arg-type]
            return latest.queue.token_number
        return None

    def _entry_response(self, row: OpdQueueEntryWithDetails) -> OpdQueueEntryResponse:
        queue = row.queue
        visit = row.visit
        return OpdQueueEntryResponse(
            id=queue.id,
            opd_visit_id=queue.opd_visit_id,
            doctor_id=queue.doctor_id,
            patient_id=visit.patient_id,
            patient_name=f"{row.patient.first_name} {row.patient.last_name}".strip(),
            token_number=queue.token_number,
            queue_date=queue.queue_date,
            status=queue.status,  # type: ignore[arg-type]
            priority=queue.priority,  # type: ignore[arg-type]
            chief_complaint=visit.chief_complaint,
            called_at=queue.called_at,
            visit_status=visit.status,  # type: ignore[arg-type]
        )


def _normalize_etag(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if trimmed.startswith('"') and trimmed.endswith('"'):
        trimmed = trimmed[1:-1]
    return trimmed or None
