"""Shared repository primitives — tenant-scoped query helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.database import set_rls_tenant_context
from app.core.exceptions import ForbiddenError
from app.models.base import active_row_filter

T = TypeVar("T")


class TenantScopedRepository:
    """
    Base repository enforcing tenant_id filter, soft-delete exclusion, and RLS context.

    Every instance binds `app.tenant_id` on the SQLAlchemy session so PostgreSQL
    RLS policies align with application-layer tenant filters.
    """

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.apply_rls_context()

    def apply_rls_context(self) -> None:
        """Set PostgreSQL session variable for RLS policies."""
        set_rls_tenant_context(self.db, self.tenant_id)

    def assert_tenant(self, entity: T) -> T:
        """Raise if entity belongs to a different tenant."""
        entity_tenant_id = getattr(entity, "tenant_id", None)
        if entity_tenant_id is not None and entity_tenant_id != self.tenant_id:
            raise ForbiddenError("Cross-tenant resource access denied", field="tenant_id")
        return entity

    def _base_query(self, model: type[T]) -> Select[tuple[T]]:
        """Build a SELECT filtered by tenant and active rows only."""
        stmt = select(model).where(model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]
        for criterion in active_row_filter(model):
            stmt = stmt.where(criterion)
        return stmt

    def get_by_id(self, model: type[T], entity_id: uuid.UUID) -> T | None:
        """Fetch one row by composite tenant scope + primary key."""
        stmt = self._base_query(model).where(model.id == entity_id)  # type: ignore[attr-defined]
        return self.db.scalars(stmt).first()

    def add(self, entity: T) -> T:
        """Insert a tenant-scoped entity after enforcing tenant_id."""
        if hasattr(entity, "tenant_id"):
            if getattr(entity, "tenant_id", None) is None:
                entity.tenant_id = self.tenant_id  # type: ignore[attr-defined]
            else:
                self.assert_tenant(entity)
        self.db.add(entity)
        return entity

    def soft_delete(self, entity: T, *, deleted_by: uuid.UUID | None = None) -> T:
        """Mark entity deleted when it supports soft-delete columns."""
        self.assert_tenant(entity)
        if hasattr(entity, "deleted_at"):
            entity.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
        if hasattr(entity, "deleted_by"):
            entity.deleted_by = deleted_by  # type: ignore[attr-defined]
        self.db.add(entity)
        return entity
