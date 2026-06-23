"""Tenant-scoped department management."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.schemas.department import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from app.models.core.department import Department
from app.models.core.staff import Staff
from app.repositories.base import TenantScopedRepository


class DepartmentService:
    """CRUD for hospital departments — scoped to JWT tenant_id."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = DepartmentRepository(db, tenant_id)
        self._location_repo = LocationRepository(db, tenant_id)
        self._setting_repo = SettingRepository(db, tenant_id)

    def list_departments(
        self,
        *,
        query: str | None = None,
        is_active: bool | None = None,
        location_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DepartmentResponse], int]:
        rows, total = self._repo.search(
            query=query,
            is_active=is_active,
            location_id=location_id,
            page=page,
            page_size=page_size,
        )
        return [DepartmentResponse.model_validate(row) for row in rows], total

    def get_department(self, department_id: uuid.UUID) -> DepartmentResponse:
        department = self._repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found", field="department_id")
        return DepartmentResponse.model_validate(department)

    def create_department(
        self,
        payload: DepartmentCreateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DepartmentResponse:
        if self._repo.get_by_code(payload.code):
            raise ConflictError("Department code already exists", field="code")

        self._validate_location(payload.location_id)
        self._validate_head_staff(payload.head_staff_id)

        department = self._repo.create(
            name=payload.name.strip(),
            code=payload.code,
            head_staff_id=payload.head_staff_id,
            location_id=payload.location_id,
            is_active=payload.is_active,
            created_by=actor_id,
        )
        self._mark_departments_added()
        response = self._response_from(department)
        self.db.commit()
        return response

    def update_department(
        self,
        department_id: uuid.UUID,
        payload: DepartmentUpdateRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DepartmentResponse:
        department = self._repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found", field="department_id")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")

        if "code" in update_data and update_data["code"] != department.code:
            existing = self._repo.get_by_code(update_data["code"])
            if existing is not None and existing.id != department.id:
                raise ConflictError("Department code already exists", field="code")

        if "location_id" in update_data:
            self._validate_location(update_data["location_id"])

        if "head_staff_id" in update_data:
            self._validate_head_staff(update_data["head_staff_id"])

        if "name" in update_data and update_data["name"] is not None:
            update_data["name"] = update_data["name"].strip()

        for key, value in update_data.items():
            setattr(department, key, value)
        department.updated_by = actor_id
        self.db.add(department)
        response = self._response_from(department)
        self.db.commit()
        return response

    def delete_department(
        self,
        department_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> DepartmentResponse:
        department = self._repo.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found", field="department_id")

        self._repo.soft_delete(department, deleted_by=actor_id)
        department.is_active = False
        self.db.add(department)
        response = self._response_from(department)
        self.db.commit()
        return response

    def _response_from(self, department: Department) -> DepartmentResponse:
        """Build API response from ORM state before session closes."""
        self.db.flush()
        return DepartmentResponse(
            id=department.id,
            tenant_id=department.tenant_id,
            name=department.name,
            code=department.code,
            head_staff_id=department.head_staff_id,
            location_id=department.location_id,
            is_active=department.is_active,
            created_at=department.created_at,
            updated_at=department.updated_at,
        )

    def _validate_location(self, location_id: uuid.UUID | None) -> None:
        if location_id is None:
            return
        if self._location_repo.get_by_id(location_id) is None:
            raise NotFoundError("Location not found", field="location_id")

    def _validate_head_staff(self, staff_id: uuid.UUID | None) -> None:
        if staff_id is None:
            return
        staff = TenantScopedRepository.get_by_id(self._repo, Staff, staff_id)
        if staff is None:
            raise NotFoundError("Staff not found", field="head_staff_id")

    def _mark_departments_added(self) -> None:
        progress = self._setting_repo.get_by_key("onboarding_progress")
        if progress is None:
            return
        value = dict(progress.setting_value)
        if not value.get("departments_added"):
            value["departments_added"] = True
            progress.setting_value = value
            self.db.add(progress)
