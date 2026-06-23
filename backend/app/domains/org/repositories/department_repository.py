"""core.departments data access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select

from app.models.core.department import Department
from app.repositories.base import TenantScopedRepository


class DepartmentRepository(TenantScopedRepository):
    def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        return super().get_by_id(Department, department_id)

    def get_by_code(self, code: str) -> Department | None:
        stmt = self._base_query(Department).where(Department.code == code.upper())
        return self.db.scalars(stmt).first()

    def create(self, **kwargs: object) -> Department:
        department = Department(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(department)
        return department

    def search(
        self,
        *,
        query: str | None = None,
        is_active: bool | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Department], int]:
        stmt = self._base_query(Department)
        count_stmt = select(func.count()).select_from(Department).where(
            Department.tenant_id == self.tenant_id,
            Department.deleted_at.is_(None),
        )

        if is_active is not None:
            stmt = stmt.where(Department.is_active.is_(is_active))
            count_stmt = count_stmt.where(Department.is_active.is_(is_active))

        if location_id is not None:
            stmt = stmt.where(Department.location_id == location_id)
            count_stmt = count_stmt.where(Department.location_id == location_id)

        if query:
            pattern = f"%{query.strip()}%"
            criterion = or_(
                Department.name.ilike(pattern),
                Department.code.ilike(pattern),
            )
            stmt = stmt.where(criterion)
            count_stmt = count_stmt.where(criterion)

        total = self.db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Department.name).offset(offset).limit(page_size)
        return list(self.db.scalars(stmt).all()), int(total)
