"""Tenant-scoped doctor profile management."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository, DoctorWithStaff
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.org.schemas.doctor import DoctorCreateRequest, DoctorResponse, DoctorUpdateRequest


class DoctorService:
    """CRUD for doctor profiles extending staff — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = DoctorRepository(db, tenant_id)
        self._staff_repo = StaffRepository(db, tenant_id)
        self._dept_repo = DepartmentRepository(db, tenant_id)

    def list_doctors(
        self,
        *,
        query: str | None = None,
        specialization: str | None = None,
        department_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        is_available: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DoctorResponse], int]:
        rows, total = self._repo.search(
            query=query,
            specialization=specialization,
            department_id=department_id,
            location_id=location_id,
            is_available=is_available,
            page=page,
            page_size=page_size,
        )
        return [self._response_from_row(row) for row in rows], total

    def get_doctor(self, doctor_id: uuid.UUID) -> DoctorResponse:
        row = self._repo.get_with_staff(doctor_id)
        if row is None:
            raise NotFoundError("Doctor not found", field="doctor_id")
        return self._response_from_row(row)

    def create_doctor(
        self,
        payload: DoctorCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DoctorResponse:
        staff = self._staff_repo.get_by_id(payload.staff_id)
        if staff is None:
            raise NotFoundError("Staff not found", field="staff_id")
        if staff.status == "terminated":
            raise ValidationError("Cannot create doctor for terminated staff", field="staff_id")
        if self._repo.get_by_staff_id(payload.staff_id):
            raise ConflictError("Staff member already has a doctor profile", field="staff_id")

        department_id = payload.department_id or staff.department_id
        self._validate_department(department_id)

        doctor = self._repo.create(
            staff_id=payload.staff_id,
            registration_number=payload.registration_number,
            specialization=payload.specialization.strip(),
            qualification=payload.qualification,
            consultation_fee=payload.consultation_fee,
            follow_up_fee=payload.follow_up_fee,
            department_id=department_id,
            bio=payload.bio,
            is_available=payload.is_available,
            created_by=actor_id,
        )
        self.db.flush()
        row = self._repo.get_with_staff(doctor.id)
        assert row is not None
        response = self._response_from_row(row)
        self.db.commit()
        return response

    def update_doctor(
        self,
        doctor_id: uuid.UUID,
        payload: DoctorUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DoctorResponse:
        doctor = self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor not found", field="doctor_id")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        if "department_id" in update_data:
            self._validate_department(update_data["department_id"])

        if "specialization" in update_data and update_data["specialization"] is not None:
            update_data["specialization"] = update_data["specialization"].strip()

        for key, value in update_data.items():
            setattr(doctor, key, value)
        doctor.updated_by = actor_id
        self.db.add(doctor)

        row = self._repo.get_with_staff(doctor.id)
        assert row is not None
        response = self._response_from_row(row)
        self.db.commit()
        return response

    def delete_doctor(
        self,
        doctor_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DoctorResponse:
        doctor = self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor not found", field="doctor_id")

        row = self._repo.get_with_staff(doctor.id)
        assert row is not None

        self._repo.soft_delete(doctor, deleted_by=actor_id)
        doctor.is_available = False
        row.doctor.is_available = False
        self.db.add(doctor)
        response = self._response_from_row(row)
        self.db.commit()
        return response

    def _response_from_row(self, row: DoctorWithStaff) -> DoctorResponse:
        self.db.flush()
        department_name = None
        if row.doctor.department_id is not None:
            department = self._dept_repo.get_by_id(row.doctor.department_id)
            if department is not None:
                department_name = department.name

        return DoctorResponse(
            id=row.doctor.id,
            tenant_id=row.doctor.tenant_id,
            staff_id=row.doctor.staff_id,
            first_name=row.staff.first_name,
            last_name=row.staff.last_name,
            employee_code=row.staff.employee_code,
            registration_number=row.doctor.registration_number,
            specialization=row.doctor.specialization,
            qualification=row.doctor.qualification,
            consultation_fee=row.doctor.consultation_fee,
            follow_up_fee=row.doctor.follow_up_fee,
            department_id=row.doctor.department_id,
            department_name=department_name,
            bio=row.doctor.bio,
            is_available=row.doctor.is_available,
            created_at=row.doctor.created_at,
            updated_at=row.doctor.updated_at,
        )

    def _validate_department(self, department_id: uuid.UUID | None) -> None:
        if department_id is None:
            return
        if self._dept_repo.get_by_id(department_id) is None:
            raise NotFoundError("Department not found", field="department_id")
