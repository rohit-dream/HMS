"""Queue board ETag fingerprint for polling."""

from __future__ import annotations

import hashlib
import json

from app.domains.clinical.schemas.opd.queue import OpdQueueBoardResponse


def compute_queue_etag(board: OpdQueueBoardResponse) -> str:
    """Stable hash of queue board state for If-None-Match polling."""
    fingerprint = {
        "doctor_id": str(board.doctor_id),
        "queue_date": board.queue_date.isoformat(),
        "current_token": board.current_token,
        "waiting_count": board.waiting_count,
        "entries": [
            {
                "id": str(entry.id),
                "status": entry.status,
                "token_number": entry.token_number,
                "priority": entry.priority,
                "called_at": entry.called_at.isoformat() if entry.called_at else None,
                "visit_status": entry.visit_status,
            }
            for entry in board.entries
        ],
    }
    payload = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
