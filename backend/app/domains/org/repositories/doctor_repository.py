"""core.doctors data access."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, or_, select

from app.models.core.doctor import Doctor
from app.models.core.staff import Staff
from app.repositories.base import TenantScopedRepository


@dataclass(frozen=True)
class DoctorWithStaff:
    doctor: Doctor
    staff: Staff


class DoctorRepository(TenantScopedRepository):
    def get_by_id(self, doctor_id: uuid.UUID) -> Doctor | None:
        return super().get_by_id(Doctor, doctor_id)

    def get_by_staff_id(self, staff_id: uuid.UUID) -> Doctor | None:
        stmt = self._base_query(Doctor).where(Doctor.staff_id == staff_id)
        return self.db.scalars(stmt).first()

    def get_with_staff(self, doctor_id: uuid.UUID) -> DoctorWithStaff | None:
        stmt = (
            select(Doctor, Staff)
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(
                Doctor.tenant_id == self.tenant_id,
                Doctor.id == doctor_id,
                Doctor.deleted_at.is_(None),
                Staff.deleted_at.is_(None),
            )
        )
        row = self.db.execute(stmt).first()
        if row is None:
            return None
        return DoctorWithStaff(doctor=row[0], staff=row[1])

    def create(self, **kwargs: object) -> Doctor:
        doctor = Doctor(tenant_id=self.tenant_id, **kwargs)  # type: ignore[arg-type]
        self.db.add(doctor)
        return doctor

    def search(
        self,
        *,
        query: str | None = None,
        specialization: str | None = None,
        department_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        is_available: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DoctorWithStaff], int]:
        base_filters = [
            Doctor.tenant_id == self.tenant_id,
            Doctor.deleted_at.is_(None),
            Staff.deleted_at.is_(None),
        ]

        if is_available is not None:
            base_filters.append(Doctor.is_available.is_(is_available))

        if department_id is not None:
            base_filters.append(Doctor.department_id == department_id)

        if location_id is not None:
            base_filters.append(Staff.location_id == location_id)

        if specialization:
            base_filters.append(Doctor.specialization.ilike(f"%{specialization.strip()}%"))

        if query:
            pattern = f"%{query.strip()}%"
            base_filters.append(
                or_(
                    Staff.first_name.ilike(pattern),
                    Staff.last_name.ilike(pattern),
                    Doctor.specialization.ilike(pattern),
                    Doctor.registration_number.ilike(pattern),
                )
            )

        count_stmt = (
            select(func.count())
            .select_from(Doctor)
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(*base_filters)
        )
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Doctor, Staff)
            .join(
                Staff,
                (Doctor.tenant_id == Staff.tenant_id) & (Doctor.staff_id == Staff.id),
            )
            .where(*base_filters)
            .order_by(Staff.last_name, Staff.first_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = [DoctorWithStaff(doctor=doc, staff=st) for doc, st in self.db.execute(stmt).all()]
        return rows, int(total)
