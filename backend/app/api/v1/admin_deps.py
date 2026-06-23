"""Admin API dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.authorization import AuthorizationContext, get_authorization_context
from app.core.database import get_db
from app.domains.identity.services.user_management_service import UserManagementService
from app.domains.org.services.department_service import DepartmentService
from app.domains.org.services.doctor_schedule_service import DoctorScheduleService
from app.domains.org.services.doctor_service import DoctorService
from app.domains.org.services.staff_service import StaffService


def get_user_management_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> UserManagementService:
    return UserManagementService(db, ctx.user.tenant_id)


def get_department_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> DepartmentService:
    return DepartmentService(db, ctx.user.tenant_id)


def get_staff_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> StaffService:
    return StaffService(db, ctx.user.tenant_id)


def get_doctor_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> DoctorService:
    return DoctorService(db, ctx.user.tenant_id)


def get_doctor_schedule_service(
    ctx: AuthorizationContext = Depends(get_authorization_context),
    db: Session = Depends(get_db),
) -> DoctorScheduleService:
    return DoctorScheduleService(db, ctx.user.tenant_id)
