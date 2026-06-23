"""Org domain repositories."""

from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.org.repositories.staff_repository import StaffRepository

__all__ = [
    "DepartmentRepository",
    "DoctorRepository",
    "DoctorScheduleRepository",
    "StaffRepository",
]
