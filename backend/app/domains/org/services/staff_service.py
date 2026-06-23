"""Tenant-scoped staff management."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.identity.repositories.user_repository import UserRepository
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.org.schemas.staff import StaffCreateRequest, StaffResponse, StaffUpdateRequest
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from app.models.core.staff import Staff


class StaffService:
    """CRUD for employee records — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = StaffRepository(db, tenant_id)
        self._dept_repo = DepartmentRepository(db, tenant_id)
        self._location_repo = LocationRepository(db, tenant_id)
        self._user_repo = UserRepository(db, tenant_id)
        self._setting_repo = SettingRepository(db, tenant_id)

    def list_staff(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[StaffResponse], int]:
        rows, total = self._repo.search(
            query=query,
            status=status,
            department_id=department_id,
            location_id=location_id,
            page=page,
            page_size=page_size,
        )
        return [self._response_from(row) for row in rows], total

    def get_staff(self, staff_id: uuid.UUID) -> StaffResponse:
        staff = self._repo.get_by_id(staff_id)
        if staff is None:
            raise NotFoundError("Staff not found", field="staff_id")
        return self._response_from(staff)

    def create_staff(
        self,
        payload: StaffCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> StaffResponse:
        if self._repo.get_by_employee_code(payload.employee_code):
            raise ConflictError("Employee code already exists", field="employee_code")

        self._validate_department(payload.department_id)
        self._validate_location(payload.location_id)
        self._validate_dates(payload.joining_date, payload.leaving_date)

        staff = self._repo.create(
            employee_code=payload.employee_code,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            email=str(payload.email).lower() if payload.email else None,
            phone=payload.phone,
            department_id=payload.department_id,
            designation=payload.designation,
            joining_date=payload.joining_date,
            leaving_date=payload.leaving_date,
            status=payload.status,
            location_id=payload.location_id,
            created_by=actor_id,
        )
        self.db.flush()

        if payload.user_id is not None:
            self._link_user(staff.id, payload.user_id)

        self._mark_staff_invited()
        response = self._response_from(staff)
        self.db.commit()
        return response

    def update_staff(
        self,
        staff_id: uuid.UUID,
        payload: StaffUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> StaffResponse:
        staff = self._repo.get_by_id(staff_id)
        if staff is None:
            raise NotFoundError("Staff not found", field="staff_id")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data and "user_id" not in payload.model_fields_set:
            raise ValidationError("No fields to update", field="body")

        if "employee_code" in update_data and update_data["employee_code"] != staff.employee_code:
            existing = self._repo.get_by_employee_code(update_data["employee_code"])
            if existing is not None and existing.id != staff.id:
                raise ConflictError("Employee code already exists", field="employee_code")

        if "department_id" in update_data:
            self._validate_department(update_data["department_id"])

        if "location_id" in update_data:
            self._validate_location(update_data["location_id"])

        joining_date = update_data.get("joining_date", staff.joining_date)
        leaving_date = update_data.get("leaving_date", staff.leaving_date)
        if "joining_date" in update_data or "leaving_date" in update_data:
            self._validate_dates(joining_date, leaving_date)

        if "email" in update_data and update_data["email"] is not None:
            update_data["email"] = str(update_data["email"]).lower()

        for key in ("first_name", "last_name"):
            if key in update_data and update_data[key] is not None:
                update_data[key] = update_data[key].strip()

        for key, value in update_data.items():
            if key == "user_id":
                continue
            setattr(staff, key, value)

        if "user_id" in payload.model_fields_set:
            if payload.user_id is None:
                self._repo.unlink_staff_from_users(staff.id)
            else:
                self._link_user(staff.id, payload.user_id)

        staff.updated_by = actor_id
        self.db.add(staff)
        response = self._response_from(staff)
        self.db.commit()
        return response

    def delete_staff(
        self,
        staff_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> StaffResponse:
        staff = self._repo.get_by_id(staff_id)
        if staff is None:
            raise NotFoundError("Staff not found", field="staff_id")

        self._repo.soft_delete(staff, deleted_by=actor_id)
        staff.status = "terminated"
        if staff.leaving_date is None:
            staff.leaving_date = date.today()
        self._repo.unlink_staff_from_users(staff.id)
        self.db.add(staff)
        response = self._response_from(staff)
        self.db.commit()
        return response

    def _response_from(self, staff: Staff) -> StaffResponse:
        self.db.flush()
        department_name = None
        if staff.department_id is not None:
            department = self._dept_repo.get_by_id(staff.department_id)
            if department is not None:
                department_name = department.name

        return StaffResponse(
            id=staff.id,
            tenant_id=staff.tenant_id,
            employee_code=staff.employee_code,
            first_name=staff.first_name,
            last_name=staff.last_name,
            email=staff.email,
            phone=staff.phone,
            department_id=staff.department_id,
            department_name=department_name,
            designation=staff.designation,
            status=staff.status,
            joining_date=staff.joining_date,
            leaving_date=staff.leaving_date,
            location_id=staff.location_id,
            is_doctor=self._repo.is_doctor(staff.id),
            user_id=self._repo.get_linked_user_id(staff.id),
            created_at=staff.created_at,
            updated_at=staff.updated_at,
        )

    def _validate_department(self, department_id: uuid.UUID | None) -> None:
        if department_id is None:
            return
        if self._dept_repo.get_by_id(department_id) is None:
            raise NotFoundError("Department not found", field="department_id")

    def _validate_location(self, location_id: uuid.UUID | None) -> None:
        if location_id is None:
            return
        if self._location_repo.get_by_id(location_id) is None:
            raise NotFoundError("Location not found", field="location_id")

    @staticmethod
    def _validate_dates(joining_date: date, leaving_date: date | None) -> None:
        if leaving_date is not None and leaving_date < joining_date:
            raise ValidationError("leaving_date cannot be before joining_date", field="leaving_date")

    def _link_user(self, staff_id: uuid.UUID, user_id: uuid.UUID) -> None:
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", field="user_id")
        if user.staff_id is not None and user.staff_id != staff_id:
            raise ConflictError("User already linked to another staff record", field="user_id")
        user.staff_id = staff_id
        self.db.add(user)

    def _mark_staff_invited(self) -> None:
        progress = self._setting_repo.get_by_key("onboarding_progress")
        if progress is None:
            return
        value = dict(progress.setting_value)
        if not value.get("staff_invited"):
            value["staff_invited"] = True
            progress.setting_value = value
            self.db.add(progress)
