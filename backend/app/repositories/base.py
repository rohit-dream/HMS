"""Shared repository primitives — tenant-scoped query helpers."""

from __future__ import annotations

import uuid
from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.base import active_row_filter

T = TypeVar("T")


class TenantScopedRepository:
    """
    Base repository enforcing tenant_id filter and soft-delete exclusion.

    Business repositories extend this class in domain modules.
    """

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

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
