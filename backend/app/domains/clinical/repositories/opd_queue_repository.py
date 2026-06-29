"""clinical.opd_queue data access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select

from app.models.clinical.opd import OpdQueue, OpdVisit
from app.models.core.patient import Patient
from app.repositories.base import TenantScopedRepository


@dataclass(frozen=True)
class OpdQueueEntryWithDetails:
    queue: OpdQueue
    visit: OpdVisit
    patient: Patient


class OpdQueueRepository(TenantScopedRepository):
    VALID_STATUSES = frozenset(
        {"waiting", "called", "in_consultation", "completed", "skipped"}
    )
    ACTIVE_STATUSES = frozenset({"waiting", "called", "in_consultation"})

    def get_by_id(self, queue_id: uuid.UUID) -> OpdQueue | None:
        return super().get_by_id(OpdQueue, queue_id)

    def get_with_details(self, queue_id: uuid.UUID) -> OpdQueueEntryWithDetails | None:
        stmt = (
            select(OpdQueue, OpdVisit, Patient)
            .join(
                OpdVisit,
                (OpdQueue.tenant_id == OpdVisit.tenant_id)
                & (OpdQueue.opd_visit_id == OpdVisit.id),
            )
            .join(
                Patient,
                (OpdVisit.tenant_id == Patient.tenant_id) & (OpdVisit.patient_id == Patient.id),
            )
            .where(
                OpdQueue.tenant_id == self.tenant_id,
                OpdQueue.id == queue_id,
                OpdQueue.deleted_at.is_(None),
                OpdVisit.deleted_at.is_(None),
                Patient.deleted_at.is_(None),
            )
        )
        row = self.db.execute(stmt).first()
        if row is None:
            return None
        return OpdQueueEntryWithDetails(queue=row[0], visit=row[1], patient=row[2])

    def get_active_for_visit(self, visit_id: uuid.UUID) -> OpdQueue | None:
        stmt = self._base_query(OpdQueue).where(
            OpdQueue.opd_visit_id == visit_id,
            OpdQueue.status.notin_(("completed", "skipped")),
        )
        return self.db.scalars(stmt).first()

    def get_active_with_details_for_visit(
        self,
        visit_id: uuid.UUID,
    ) -> OpdQueueEntryWithDetails | None:
        entry = self.get_active_for_visit(visit_id)
        if entry is None:
            return None
        return self.get_with_details(entry.id)

    def list_board_entries(
        self,
        *,
        doctor_id: uuid.UUID,
        queue_date: date,
        location_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[OpdQueueEntryWithDetails]:
        filters = [
            OpdQueue.tenant_id == self.tenant_id,
            OpdQueue.doctor_id == doctor_id,
            OpdQueue.queue_date == queue_date,
            OpdQueue.deleted_at.is_(None),
            OpdVisit.deleted_at.is_(None),
            Patient.deleted_at.is_(None),
            OpdQueue.status.notin_(("completed", "skipped")),
        ]
        if location_id is not None:
            filters.append(OpdVisit.location_id == location_id)
        if status is not None:
            filters.append(OpdQueue.status == status)

        stmt = (
            select(OpdQueue, OpdVisit, Patient)
            .join(
                OpdVisit,
                (OpdQueue.tenant_id == OpdVisit.tenant_id)
                & (OpdQueue.opd_visit_id == OpdVisit.id),
            )
            .join(
                Patient,
                (OpdVisit.tenant_id == Patient.tenant_id) & (OpdVisit.patient_id == Patient.id),
            )
            .where(*filters)
            .order_by(OpdQueue.token_number)
        )
        return [
            OpdQueueEntryWithDetails(queue=queue, visit=visit, patient=patient)
            for queue, visit, patient in self.db.execute(stmt).all()
        ]

    def list_waiting_entries(
        self,
        *,
        doctor_id: uuid.UUID,
        queue_date: date,
    ) -> list[OpdQueue]:
        stmt = (
            self._base_query(OpdQueue)
            .where(
                OpdQueue.doctor_id == doctor_id,
                OpdQueue.queue_date == queue_date,
                OpdQueue.status == "waiting",
            )
            .order_by(OpdQueue.token_number)
        )
        return list(self.db.scalars(stmt).all())

    def next_token_number(self, *, doctor_id: uuid.UUID, queue_date: date) -> int:
        stmt = select(func.coalesce(func.max(OpdQueue.token_number), 0)).where(
            OpdQueue.tenant_id == self.tenant_id,
            OpdQueue.doctor_id == doctor_id,
            OpdQueue.queue_date == queue_date,
            OpdQueue.deleted_at.is_(None),
        )
        current_max = self.db.scalar(stmt) or 0
        return int(current_max) + 1

    def create(self, **kwargs: object) -> OpdQueue:
        entry = OpdQueue(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(entry)
        return entry

    def reassign_waiting_token_numbers(
        self,
        entries: list[OpdQueue],
        *,
        actor_id: uuid.UUID | None = None,
    ) -> None:
        for index, entry in enumerate(entries, start=1):
            entry.token_number = index
            entry.updated_by = actor_id
            self.db.add(entry)
