"""OPD e-prescription lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.clinical.repositories.opd_prescription_repository import (
    OpdPrescriptionRepository,
    OpdPrescriptionWithItems,
)
from app.domains.clinical.repositories.opd_visit_repository import OpdVisitRepository
from app.domains.clinical.schemas.opd.prescription import (
    OpdPrescriptionCreateRequest,
    OpdPrescriptionItemResponse,
    OpdPrescriptionResponse,
)
from app.models.clinical.opd import OpdPrescription, OpdPrescriptionItem

TERMINAL_VISIT_STATUSES = frozenset({"completed", "cancelled"})


class OpdPrescriptionService:
    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = OpdPrescriptionRepository(db, tenant_id)
        self._visit_repo = OpdVisitRepository(db, tenant_id)

    def create_prescription(
        self,
        visit_id: uuid.UUID,
        payload: OpdPrescriptionCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdPrescriptionResponse:
        visit = self._visit_repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status in TERMINAL_VISIT_STATUSES:
            raise ConflictError("Cannot prescribe on a completed or cancelled visit", field="status")
        if visit.status != "in_consultation":
            raise ConflictError(
                "Visit must be in consultation to add prescription",
                field="status",
            )

        prescription_number = self._repo.generate_prescription_number()
        now = datetime.now(UTC)
        prescription = self._repo.create_prescription(
            opd_visit_id=visit_id,
            patient_id=visit.patient_id,
            doctor_id=visit.doctor_id,
            prescription_number=prescription_number,
            prescribed_at=now,
            status="active",
            notes=payload.notes,
            created_by=actor_id,
        )
        self.db.flush()

        items: list[OpdPrescriptionItem] = []
        for item_payload in payload.items:
            item = self._repo.create_item(
                prescription_id=prescription.id,
                medicine_id=item_payload.medicine_id,
                medicine_name=item_payload.medicine_name,
                dosage=item_payload.dosage,
                frequency=item_payload.frequency,
                duration=item_payload.duration,
                route=item_payload.route,
                instructions=item_payload.instructions,
                quantity=item_payload.quantity,
                created_by=actor_id,
            )
            items.append(item)

        self.db.flush()
        response = self._response_from(
            OpdPrescriptionWithItems(prescription=prescription, items=items)
        )
        self.db.commit()
        return response

    def list_prescriptions(self, visit_id: uuid.UUID) -> list[OpdPrescriptionResponse]:
        if self._visit_repo.get_by_id(visit_id) is None:
            raise NotFoundError("OPD visit not found", field="visit_id")

        rows = self._repo.list_for_visit(visit_id)
        responses = [self._response_from(row) for row in rows]
        self.db.commit()
        return responses

    def get_prescription(
        self,
        visit_id: uuid.UUID,
        prescription_id: uuid.UUID,
    ) -> OpdPrescriptionResponse:
        if self._visit_repo.get_by_id(visit_id) is None:
            raise NotFoundError("OPD visit not found", field="visit_id")

        row = self._repo.get_with_items(prescription_id)
        if row is None or row.prescription.opd_visit_id != visit_id:
            raise NotFoundError("Prescription not found", field="prescription_id")

        response = self._response_from(row)
        self.db.commit()
        return response

    def _response_from(self, row: OpdPrescriptionWithItems) -> OpdPrescriptionResponse:
        prescription = row.prescription
        return OpdPrescriptionResponse(
            id=prescription.id,
            opd_visit_id=prescription.opd_visit_id,
            patient_id=prescription.patient_id,
            doctor_id=prescription.doctor_id,
            prescription_number=prescription.prescription_number,
            prescribed_at=prescription.prescribed_at,
            status=prescription.status,  # type: ignore[arg-type]
            notes=prescription.notes,
            items=[self._item_response(item) for item in row.items],
        )

    def _item_response(self, item: OpdPrescriptionItem) -> OpdPrescriptionItemResponse:
        return OpdPrescriptionItemResponse(
            id=item.id,
            medicine_id=item.medicine_id,
            medicine_name=item.medicine_name,
            dosage=item.dosage,
            frequency=item.frequency,
            duration=item.duration,
            route=item.route,  # type: ignore[arg-type]
            instructions=item.instructions,
            quantity=item.quantity,
        )
