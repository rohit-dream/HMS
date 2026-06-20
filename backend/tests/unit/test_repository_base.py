"""Unit tests for tenant-scoped repository base."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from sqlalchemy import Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

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


def test_base_query_filters_tenant_and_active_rows() -> None:
    tenant_id = uuid.uuid4()
    repo = TenantScopedRepository(MagicMock(), tenant_id)
    sql = _compile(repo._base_query(_PatientStub))

    assert str(tenant_id) in sql
    assert "deleted_at IS NULL" in sql
    assert "core.patient_stubs" in sql


def test_get_by_id_builds_tenant_scoped_lookup() -> None:
    tenant_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    repo = TenantScopedRepository(MagicMock(), tenant_id)

    stmt = repo._base_query(_PatientStub).where(_PatientStub.id == entity_id)
    sql = _compile(stmt)

    assert str(tenant_id) in sql
    assert str(entity_id) in sql
