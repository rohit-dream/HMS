"""Aggregates all v1 API routers."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    admin_departments,
    admin_users,
    appointments,
    auth,
    doctor_schedules,
    doctors,
    health,
    hospital,
    opd,
    patients,
    platform,
    subscription,
    staff,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(hospital.router)
api_router.include_router(admin.router)
api_router.include_router(admin_departments.router)
api_router.include_router(admin_users.router)
api_router.include_router(staff.router)
api_router.include_router(doctors.router)
api_router.include_router(doctor_schedules.router)
api_router.include_router(patients.router)
api_router.include_router(appointments.router)
api_router.include_router(opd.router)
api_router.include_router(subscription.router)
