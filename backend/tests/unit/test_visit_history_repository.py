"""Unit tests — patient visit history repository."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from app.domains.patients.repositories.visit_history_repository import PatientVisitHistoryRepository


def test_list_for_patient_returns_empty_when_opd_table_missing() -> None:
    db = MagicMock()
    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    db.execute.return_value.scalar_one.return_value = False

    repo = PatientVisitHistoryRepository(db, tenant_id)
    items, total = repo.list_for_patient(patient_id)

    assert items == []
    assert total == 0
