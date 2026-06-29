"""OPD vitals recording."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.clinical.repositories.opd_visit_repository import OpdVisitRepository
from app.domains.clinical.repositories.opd_vitals_repository import OpdVitalsRepository
from app.domains.clinical.schemas.opd.vitals import OpdVitalsCreateRequest, OpdVitalsResponse
from app.models.clinical.opd import OpdVitals

TERMINAL_VISIT_STATUSES = frozenset({"completed", "cancelled"})


def calculate_bmi(*, weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    height_m = height_cm / Decimal("100")
    if height_m <= 0:
        raise ValidationError("height_cm must be greater than zero", field="height_cm")
    bmi = weight_kg / (height_m * height_m)
    return bmi.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


class OpdVitalsService:
    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = OpdVitalsRepository(db, tenant_id)
        self._visit_repo = OpdVisitRepository(db, tenant_id)

    def record_vitals(
        self,
        visit_id: uuid.UUID,
        payload: OpdVitalsCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> OpdVitalsResponse:
        visit = self._visit_repo.get_by_id(visit_id)
        if visit is None:
            raise NotFoundError("OPD visit not found", field="visit_id")
        if visit.status in TERMINAL_VISIT_STATUSES:
            raise ConflictError(
                "Cannot record vitals on a completed or cancelled visit",
                field="status",
            )

        data = payload.model_dump()
        if not any(
            data.get(field) is not None
            for field in (
                "blood_pressure_systolic",
                "blood_pressure_diastolic",
                "pulse_rate",
                "temperature",
                "respiratory_rate",
                "spo2",
                "weight_kg",
                "height_cm",
                "notes",
            )
        ):
            raise ValidationError("At least one vitals field is required", field="body")

        bmi: Decimal | None = None
        if payload.weight_kg is not None and payload.height_cm is not None:
            bmi = calculate_bmi(weight_kg=payload.weight_kg, height_cm=payload.height_cm)

        vitals = self._repo.create(
            opd_visit_id=visit_id,
            recorded_at=datetime.now(UTC),
            blood_pressure_systolic=payload.blood_pressure_systolic,
            blood_pressure_diastolic=payload.blood_pressure_diastolic,
            pulse_rate=payload.pulse_rate,
            temperature=payload.temperature,
            respiratory_rate=payload.respiratory_rate,
            spo2=payload.spo2,
            weight_kg=payload.weight_kg,
            height_cm=payload.height_cm,
            bmi=bmi,
            notes=payload.notes,
            created_by=actor_id,
        )
        self.db.flush()
        response = self._response_from(vitals)
        self.db.commit()
        return response

    def list_vitals(self, visit_id: uuid.UUID) -> list[OpdVitalsResponse]:
        if self._visit_repo.get_by_id(visit_id) is None:
            raise NotFoundError("OPD visit not found", field="visit_id")

        rows = self._repo.list_for_visit(visit_id)
        responses = [self._response_from(row) for row in rows]
        self.db.commit()
        return responses

    def _response_from(self, vitals: OpdVitals) -> OpdVitalsResponse:
        return OpdVitalsResponse(
            id=vitals.id,
            opd_visit_id=vitals.opd_visit_id,
            recorded_at=vitals.recorded_at,
            recorded_by_user_id=vitals.created_by,
            blood_pressure_systolic=vitals.blood_pressure_systolic,
            blood_pressure_diastolic=vitals.blood_pressure_diastolic,
            pulse_rate=vitals.pulse_rate,
            temperature=vitals.temperature,
            temperature_unit="celsius",
            respiratory_rate=vitals.respiratory_rate,
            spo2=vitals.spo2,
            weight_kg=vitals.weight_kg,
            height_cm=vitals.height_cm,
            bmi=vitals.bmi,
            notes=vitals.notes,
        )
