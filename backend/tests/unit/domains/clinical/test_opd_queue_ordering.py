"""Unit tests — OPD queue token ordering."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock

from app.domains.clinical.repositories.opd_queue_repository import OpdQueueRepository
from app.domains.clinical.services.opd_queue_service import OpdQueueService
from app.models.clinical.opd import OpdQueue


def _waiting_entry(
    token_number: int,
    *,
    doctor_id: uuid.UUID,
    queue_date: date,
    entry_id: uuid.UUID,
) -> OpdQueue:
    return OpdQueue(
        id=entry_id,
        tenant_id=uuid.uuid4(),
        opd_visit_id=uuid.uuid4(),
        doctor_id=doctor_id,
        token_number=token_number,
        queue_date=queue_date,
        status="waiting",
        priority="normal",
    )


def test_reorder_moves_entry_to_target_position() -> None:
    doctor_id = uuid.uuid4()
    queue_date = date.today()
    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    entries = [
        _waiting_entry(1, doctor_id=doctor_id, queue_date=queue_date, entry_id=ids[0]),
        _waiting_entry(2, doctor_id=doctor_id, queue_date=queue_date, entry_id=ids[1]),
        _waiting_entry(3, doctor_id=doctor_id, queue_date=queue_date, entry_id=ids[2]),
    ]
    target = entries[2]

    db = MagicMock()
    tenant_id = uuid.uuid4()
    service = OpdQueueService(db, tenant_id)
    service._repo = MagicMock(spec=OpdQueueRepository)
    service._visit_repo = MagicMock()
    service._repo.list_waiting_entries.return_value = entries
    service._visit_repo.get_by_id.return_value = None

    service._reorder_waiting_entry(target, target_position=1, actor_id=None)

    reordered = service._repo.reassign_waiting_token_numbers.call_args.args[0]
    assert [item.id for item in reordered] == [ids[2], ids[0], ids[1]]
