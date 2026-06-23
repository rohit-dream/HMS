"""core.staff data access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select

from app.models.core.doctor import Doctor
from app.models.core.staff import Staff
from app.models.core.user import User
from app.repositories.base import TenantScopedRepository


class StaffRepository(TenantScopedRepository):
    def get_by_id(self, staff_id: uuid.UUID) -> Staff | None:
        return super().get_by_id(Staff, staff_id)

    def get_by_employee_code(self, employee_code: str) -> Staff | None:
        stmt = self._base_query(Staff).where(Staff.employee_code == employee_code.upper())
        return self.db.scalars(stmt).first()

    def create(self, **kwargs: object) -> Staff:
        staff = Staff(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(staff)
        return staff

    def search(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Staff], int]:
        stmt = self._base_query(Staff)
        count_stmt = select(func.count()).select_from(Staff).where(
            Staff.tenant_id == self.tenant_id,
            Staff.deleted_at.is_(None),
        )

        if status:
            stmt = stmt.where(Staff.status == status)
            count_stmt = count_stmt.where(Staff.status == status)

        if department_id is not None:
            stmt = stmt.where(Staff.department_id == department_id)
            count_stmt = count_stmt.where(Staff.department_id == department_id)

        if location_id is not None:
            stmt = stmt.where(Staff.location_id == location_id)
            count_stmt = count_stmt.where(Staff.location_id == location_id)

        if query:
            pattern = f"%{query.strip()}%"
            criterion = or_(
                Staff.first_name.ilike(pattern),
                Staff.last_name.ilike(pattern),
                Staff.email.ilike(pattern),
                Staff.employee_code.ilike(pattern),
            )
            stmt = stmt.where(criterion)
            count_stmt = count_stmt.where(criterion)

        total = self.db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Staff.last_name, Staff.first_name).offset(offset).limit(page_size)
        return list(self.db.scalars(stmt).all()), int(total)

    def get_linked_user_id(self, staff_id: uuid.UUID) -> uuid.UUID | None:
        stmt = select(User.id).where(
            User.tenant_id == self.tenant_id,
            User.staff_id == staff_id,
            User.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first()

    def is_doctor(self, staff_id: uuid.UUID) -> bool:
        stmt = select(Doctor.id).where(
            Doctor.tenant_id == self.tenant_id,
            Doctor.staff_id == staff_id,
            Doctor.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first() is not None

    def unlink_staff_from_users(self, staff_id: uuid.UUID) -> None:
        stmt = select(User).where(
            User.tenant_id == self.tenant_id,
            User.staff_id == staff_id,
            User.deleted_at.is_(None),
        )
        for user in self.db.scalars(stmt).all():
            user.staff_id = None
            self.db.add(user)
