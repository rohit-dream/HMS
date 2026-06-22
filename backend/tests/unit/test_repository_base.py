"""Unit tests for tenant-scoped repository base."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.core.exceptions import ForbiddenError
from app.models.base import TenantAuditableEntity
from app.repositories.base import TenantScopedRepository


class _PatientStub(TenantAuditableEntity):
    __tablename__ = "patient_stubs"
    __table_args__ = {"schema": "core"}

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[int] = mapped_column(Integer, nullable=False)


def _compile(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@patch("app.repositories.base.set_rls_tenant_context")
def test_init_binds_rls_context(mock_set_rls) -> None:
    tenant_id = uuid.uuid4()
    db = MagicMock()
    TenantScopedRepository(db, tenant_id)
    mock_set_rls.assert_called_once_with(db, tenant_id)


@patch("app.repositories.base.set_rls_tenant_context")
def test_base_query_filters_tenant_and_active_rows(mock_set_rls) -> None:
    tenant_id = uuid.uuid4()
    repo = TenantScopedRepository(MagicMock(), tenant_id)
    sql = _compile(repo._base_query(_PatientStub))

    assert str(tenant_id) in sql
    assert "deleted_at IS NULL" in sql
    assert "core.patient_stubs" in sql


@patch("app.repositories.base.set_rls_tenant_context")
def test_get_by_id_builds_tenant_scoped_lookup(mock_set_rls) -> None:
    tenant_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    repo = TenantScopedRepository(MagicMock(), tenant_id)

    stmt = repo._base_query(_PatientStub).where(_PatientStub.id == entity_id)
    sql = _compile(stmt)

    assert str(tenant_id) in sql
    assert str(entity_id) in sql


@patch("app.repositories.base.set_rls_tenant_context")
def test_add_stamps_missing_tenant_id(mock_set_rls) -> None:
    tenant_id = uuid.uuid4()
    db = MagicMock()
    repo = TenantScopedRepository(db, tenant_id)
    entity = _PatientStub(name="Test", code=1)
    assert entity.tenant_id is None

    repo.add(entity)

    assert entity.tenant_id == tenant_id
    db.add.assert_called_once_with(entity)


@patch("app.repositories.base.set_rls_tenant_context")
def test_add_rejects_cross_tenant_entity(mock_set_rls) -> None:
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    repo = TenantScopedRepository(MagicMock(), tenant_id)
    entity = _PatientStub(tenant_id=other_tenant, name="Test", code=1)

    with pytest.raises(ForbiddenError):
        repo.add(entity)


@patch("app.repositories.base.set_rls_tenant_context")
def test_soft_delete_sets_deleted_at(mock_set_rls) -> None:
    tenant_id = uuid.uuid4()
    db = MagicMock()
    repo = TenantScopedRepository(db, tenant_id)
    entity = _PatientStub(tenant_id=tenant_id, name="Test", code=1)

    repo.soft_delete(entity, deleted_by=uuid.uuid4())

    assert entity.deleted_at is not None
    assert entity.deleted_at.tzinfo == UTC
    db.add.assert_called_once_with(entity)
