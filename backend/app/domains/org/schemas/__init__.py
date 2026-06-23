"""Org domain schemas."""

from app.domains.org.schemas.department import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from app.domains.org.schemas.doctor import DoctorCreateRequest, DoctorResponse, DoctorUpdateRequest
from app.domains.org.schemas.doctor_schedule import (
    DoctorScheduleCreateRequest,
    DoctorScheduleResponse,
    DoctorScheduleUpdateRequest,
)
from app.domains.org.schemas.staff import StaffCreateRequest, StaffResponse, StaffUpdateRequest

__all__ = [
    "DepartmentCreateRequest",
    "DepartmentResponse",
    "DepartmentUpdateRequest",
    "DoctorCreateRequest",
    "DoctorResponse",
    "DoctorUpdateRequest",
    "DoctorScheduleCreateRequest",
    "DoctorScheduleResponse",
    "DoctorScheduleUpdateRequest",
    "StaffCreateRequest",
    "StaffResponse",
    "StaffUpdateRequest",
]
