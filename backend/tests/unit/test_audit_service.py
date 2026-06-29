"""Unit tests — AuditService mutation writes (MVP-053)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.domains.audit.constants import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE
from app.domains.audit.sanitize import REDACTED
from app.domains.audit.services.audit_service import AuditService
from app.models.audit.audit_log import AuditLog


@pytest.fixture
def db() -> MagicMock:
    return MagicMock()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


def test_record_create_persists_sanitized_new_values(
    db: MagicMock,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    entity_id = uuid.uuid4()
    service = AuditService(db)

    row = service.record_create(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type="patient",
        entity_id=entity_id,
        new_values={"name": "Jane Doe", "password": "Secret@123"},
    )

    assert isinstance(row, AuditLog)
    assert row.tenant_id == tenant_id
    assert row.action == ACTION_CREATE
    assert row.entity_type == "patient"
    assert row.entity_id == entity_id
    assert row.new_values == {"name": "Jane Doe", "password": REDACTED}
    db.add.assert_called_once_with(row)


def test_record_update_persists_old_and_new_values(
    db: MagicMock,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    entity_id = uuid.uuid4()
    service = AuditService(db)

    row = service.record_update(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type="branch",
        entity_id=entity_id,
        old_values={"name": "Old"},
        new_values={"name": "New", "access_token": "jwt"},
    )

    assert row.action == ACTION_UPDATE
    assert row.old_values == {"name": "Old"}
    assert row.new_values == {"name": "New", "access_token": REDACTED}


def test_record_delete_persists_old_values_only(
    db: MagicMock,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    entity_id = uuid.uuid4()
    service = AuditService(db)

    row = service.record_delete(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type="user",
        entity_id=entity_id,
        old_values={"email": "gone@example.com"},
    )

    assert row.action == ACTION_DELETE
    assert row.old_values == {"email": REDACTED}
    assert row.new_values is None


def test_record_mutation_rejects_invalid_action(
    db: MagicMock,
    tenant_id: uuid.UUID,
) -> None:
    service = AuditService(db)

    with pytest.raises(ValueError, match="Invalid audit action"):
        service.record_mutation(
            tenant_id=tenant_id,
            action="archive",
            entity_type="patient",
            entity_id=uuid.uuid4(),
        )

    db.add.assert_not_called()


def test_record_phi_access_logs_view_with_metadata(
    db: MagicMock,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    patient_id = uuid.uuid4()
    service = AuditService(db)

    row = service.record_phi_access(
        tenant_id=tenant_id,
        patient_id=patient_id,
        user_id=user_id,
    )

    assert row.action == "view"
    assert row.entity_type == "patient"
    assert row.entity_id == patient_id
    assert row.audit_metadata == {"phi_access": True}
    db.add.assert_called_once_with(row)


def test_record_phi_access_includes_resource_context(
    db: MagicMock,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    patient_id = uuid.uuid4()
    visit_id = uuid.uuid4()
    service = AuditService(db)

    row = service.record_phi_access(
        tenant_id=tenant_id,
        patient_id=patient_id,
        user_id=user_id,
        resource_type="opd_visit",
        resource_id=visit_id,
    )

    assert row.audit_metadata == {
        "phi_access": True,
        "resource_type": "opd_visit",
        "resource_id": str(visit_id),
    }


def test_record_opd_visit_phi_access(
    db: MagicMock,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    patient_id = uuid.uuid4()
    visit_id = uuid.uuid4()
    service = AuditService(db)

    row = service.record_opd_visit_phi_access(
        tenant_id=tenant_id,
        patient_id=patient_id,
        visit_id=visit_id,
        user_id=user_id,
    )

    assert row.entity_type == "patient"
    assert row.entity_id == patient_id
    assert row.audit_metadata == {
        "phi_access": True,
        "resource_type": "opd_visit",
        "resource_id": str(visit_id),
    }
