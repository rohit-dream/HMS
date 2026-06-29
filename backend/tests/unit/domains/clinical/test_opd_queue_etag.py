"""Unit tests — OPD queue poll ETag."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from app.domains.clinical.queue_poll import compute_queue_etag
from app.domains.clinical.schemas.opd.queue import OpdQueueBoardResponse, OpdQueueEntryResponse


def test_compute_queue_etag_changes_when_status_changes() -> None:
    entry_id = uuid.uuid4()
    visit_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    queue_date = date.today()

    waiting_board = OpdQueueBoardResponse(
        doctor_id=doctor_id,
        queue_date=queue_date,
        current_token=None,
        waiting_count=1,
        entries=[
            OpdQueueEntryResponse(
                id=entry_id,
                opd_visit_id=visit_id,
                doctor_id=doctor_id,
                patient_id=uuid.uuid4(),
                patient_name="Anita Sharma",
                token_number=1,
                queue_date=queue_date,
                status="waiting",
                priority="normal",
                visit_status="waiting",
            )
        ],
    )
    called_board = waiting_board.model_copy(
        update={
            "entries": [
                waiting_board.entries[0].model_copy(
                    update={
                        "status": "called",
                        "called_at": datetime.now(timezone.utc),
                    }
                )
            ]
        }
    )

    assert compute_queue_etag(waiting_board) != compute_queue_etag(called_board)


def test_compute_queue_etag_is_stable_for_same_state() -> None:
    board = OpdQueueBoardResponse(
        doctor_id=uuid.uuid4(),
        queue_date=date.today(),
        current_token=2,
        waiting_count=1,
        entries=[],
    )
    assert compute_queue_etag(board) == compute_queue_etag(board)
