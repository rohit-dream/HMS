"""Unit tests for ORM base mixins and metadata."""

from __future__ import annotations

import uuid

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    AuditMixin,
    Base,
    TenantAuditableEntity,
    TenantMixin,
    UUIDPrimaryKeyMixin,
    active_row_filter,
)


class _SampleEntity(TenantAuditableEntity):
    __tablename__ = "sample_entities"
    __table_args__ = {"schema": "core"}

    name: Mapped[str] = mapped_column(String(100), nullable=False)


def test_base_metadata_has_naming_convention() -> None:
    assert "ix" in Base.metadata.naming_convention
    assert Base.metadata.naming_convention["pk"] == "pk_%(table_name)s"


def test_sample_entity_table_metadata() -> None:
    table = _SampleEntity.__table__
    assert table.schema == "core"
    assert table.name == "sample_entities"
    assert "id" in table.c
    assert "tenant_id" in table.c
    assert "deleted_at" in table.c
    assert "version" in table.c


def test_soft_delete_mixin() -> None:
    row = _SampleEntity(tenant_id=uuid.uuid4(), name="x")
    assert row.is_deleted is False
    actor = uuid.uuid4()
    row.soft_delete(by=actor)
    assert row.is_deleted is True
    assert row.deleted_by == actor
    assert row.deleted_at is not None
    assert row.deleted_at.tzinfo is not None


def test_active_row_filter_excludes_deleted() -> None:
    criteria = active_row_filter(_SampleEntity)
    assert len(criteria) == 1


def test_uuid_primary_key_server_default() -> None:
    class Entity(UUIDPrimaryKeyMixin, Base):
        __tablename__ = "uuid_only"
        __table_args__ = {"schema": "core"}

        value: Mapped[int] = mapped_column(Integer, nullable=False)

    id_col = Entity.__table__.c.id
    assert id_col.primary_key is True
    assert id_col.server_default is not None


def test_audit_mixin_columns_present_on_entity() -> None:
    for col in ("created_at", "created_by", "updated_at", "updated_by", "version"):
        assert col in _SampleEntity.__table__.c


def test_tenant_mixin_on_entity() -> None:
    assert TenantMixin in _SampleEntity.__mro__
    assert AuditMixin in _SampleEntity.__mro__
