"""OPD Pydantic schemas — API contract per docs/API_DESIGN_OPD.md."""

from app.domains.clinical.schemas.opd.notes import OpdClinicalNoteResponse, OpdNoteCreateRequest
from app.domains.clinical.schemas.opd.prescription import (
    OpdPrescriptionCreateRequest,
    OpdPrescriptionItemCreateRequest,
    OpdPrescriptionItemResponse,
    OpdPrescriptionResponse,
)
from app.domains.clinical.schemas.opd.queue import (
    OpdQueueBoardResponse,
    OpdQueueCreateRequest,
    OpdQueueEntryResponse,
    OpdQueueSkipRequest,
    OpdQueueUpdateRequest,
)
from app.domains.clinical.schemas.opd.vitals import OpdVitalsCreateRequest, OpdVitalsResponse
from app.domains.clinical.schemas.opd.visit import (
    OpdVisitCancelRequest,
    OpdVisitCompleteRequest,
    OpdVisitCreateRequest,
    OpdVisitDetailResponse,
    OpdVisitResponse,
    OpdVisitStartRequest,
    OpdVisitUpdateRequest,
)

OpdVisitDetailResponse.model_rebuild()

__all__ = [
    "OpdClinicalNoteResponse",
    "OpdNoteCreateRequest",
    "OpdPrescriptionCreateRequest",
    "OpdPrescriptionItemCreateRequest",
    "OpdPrescriptionItemResponse",
    "OpdPrescriptionResponse",
    "OpdQueueBoardResponse",
    "OpdQueueCreateRequest",
    "OpdQueueEntryResponse",
    "OpdQueueSkipRequest",
    "OpdQueueUpdateRequest",
    "OpdVitalsCreateRequest",
    "OpdVitalsResponse",
    "OpdVisitCancelRequest",
    "OpdVisitCompleteRequest",
    "OpdVisitCreateRequest",
    "OpdVisitDetailResponse",
    "OpdVisitResponse",
    "OpdVisitStartRequest",
    "OpdVisitUpdateRequest",
]
