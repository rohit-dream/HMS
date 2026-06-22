"""Aggregates all v1 API routers."""

from fastapi import APIRouter

from app.api.v1 import admin, admin_users, auth, health, hospital, patients, platform

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(platform.router)
api_router.include_router(hospital.router)
api_router.include_router(admin.router)
api_router.include_router(admin_users.router)
api_router.include_router(patients.router)
