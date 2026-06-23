"""
MVP-067 — Org structure end-to-end integration workflow (Sprint 6).

Exercises the full vertical slice via HTTP:
department → staff → doctor → schedule, including updates and soft deletes.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK, resp.text
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def test_org_structure_workflow_e2e(client: TestClient) -> None:
    """
    Sprint 6 org slice — create and wire up department, staff, doctor, and schedule.
    """
    suffix = uuid.uuid4().hex[:8]
    slug = f"org-e2e-{suffix}"
    email = f"org-e2e-{suffix}@example.com"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        location = LocationRepository(db, data["tenant_id"]).get_primary()
        assert location is not None
        location_id = location.id

    headers = _auth_headers(client, slug, email)

    dept_create = client.post(
        "/api/v1/admin/departments",
        json={
            "name": "General Medicine",
            "code": "GEN",
            "location_id": str(location_id),
            "is_active": True,
        },
        headers=headers,
    )
    assert dept_create.status_code == status.HTTP_201_CREATED, dept_create.text
    department = dept_create.json()["data"]
    department_id = department["id"]
    assert department["code"] == "GEN"

    staff_create = client.post(
        "/api/v1/staff",
        json={
            "employee_code": "DOC-E2E-001",
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": f"priya-{suffix}@example.com",
            "department_id": department_id,
            "location_id": str(location_id),
            "designation": "Consultant",
            "joining_date": "2020-01-15",
            "status": "active",
        },
        headers=headers,
    )
    assert staff_create.status_code == status.HTTP_201_CREATED, staff_create.text
    staff = staff_create.json()["data"]
    staff_id = staff["id"]
    assert staff["department_name"] == "General Medicine"
    assert staff["is_doctor"] is False

    dept_update = client.patch(
        f"/api/v1/admin/departments/{department_id}",
        json={"head_staff_id": staff_id},
        headers=headers,
    )
    assert dept_update.status_code == status.HTTP_200_OK, dept_update.text
    assert dept_update.json()["data"]["head_staff_id"] == staff_id

    doctor_create = client.post(
        "/api/v1/doctors",
        json={
            "staff_id": staff_id,
            "specialization": "General Medicine",
            "qualification": "MBBS, MD",
            "consultation_fee": "600.00",
            "follow_up_fee": "400.00",
            "department_id": department_id,
            "registration_number": f"REG-{suffix}",
            "is_available": True,
        },
        headers=headers,
    )
    assert doctor_create.status_code == status.HTTP_201_CREATED, doctor_create.text
    doctor = doctor_create.json()["data"]
    doctor_id = doctor["id"]
    assert doctor["first_name"] == "Priya"
    assert doctor["department_name"] == "General Medicine"

    staff_after_doctor = client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert staff_after_doctor.status_code == status.HTTP_200_OK
    assert staff_after_doctor.json()["data"]["is_doctor"] is True

    schedule_create = client.post(
        f"/api/v1/doctors/{doctor_id}/schedules",
        json={
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "13:00:00",
            "slot_duration_minutes": 20,
            "max_patients_per_slot": 1,
            "location_id": str(location_id),
            "is_active": True,
        },
        headers=headers,
    )
    assert schedule_create.status_code == status.HTTP_201_CREATED, schedule_create.text
    schedule = schedule_create.json()["data"]
    schedule_id = schedule["id"]

    schedule_update = client.patch(
        f"/api/v1/doctors/{doctor_id}/schedules/{schedule_id}",
        json={"end_time": "14:00:00", "slot_duration_minutes": 30},
        headers=headers,
    )
    assert schedule_update.status_code == status.HTTP_200_OK, schedule_update.text
    assert schedule_update.json()["data"]["end_time"] == "14:00:00"
    assert schedule_update.json()["data"]["slot_duration_minutes"] == 30

    doctor_update = client.patch(
        f"/api/v1/doctors/{doctor_id}",
        json={"consultation_fee": "750.00", "is_available": False},
        headers=headers,
    )
    assert doctor_update.status_code == status.HTTP_200_OK, doctor_update.text
    assert doctor_update.json()["data"]["consultation_fee"] == "750.00"
    assert doctor_update.json()["data"]["is_available"] is False

    listings = {
        "departments": client.get("/api/v1/admin/departments", headers=headers),
        "staff": client.get("/api/v1/staff", headers=headers),
        "doctors": client.get("/api/v1/doctors", headers=headers),
        "schedules": client.get(f"/api/v1/doctors/{doctor_id}/schedules", headers=headers),
    }
    for name, resp in listings.items():
        assert resp.status_code == status.HTTP_200_OK, f"{name}: {resp.text}"

    dept_ids = {item["id"] for item in listings["departments"].json()["data"]}
    staff_ids = {item["id"] for item in listings["staff"].json()["data"]}
    doctor_ids = {item["id"] for item in listings["doctors"].json()["data"]}
    schedule_ids = {item["id"] for item in listings["schedules"].json()["data"]}

    assert department_id in dept_ids
    assert staff_id in staff_ids
    assert doctor_id in doctor_ids
    assert schedule_id in schedule_ids

    schedule_delete = client.delete(
        f"/api/v1/doctors/{doctor_id}/schedules/{schedule_id}",
        headers=headers,
    )
    assert schedule_delete.status_code == status.HTTP_200_OK, schedule_delete.text
    assert schedule_delete.json()["data"]["is_active"] is False

    doctor_delete = client.delete(f"/api/v1/doctors/{doctor_id}", headers=headers)
    assert doctor_delete.status_code == status.HTTP_200_OK, doctor_delete.text
    assert doctor_delete.json()["data"]["is_available"] is False

    staff_delete = client.delete(f"/api/v1/staff/{staff_id}", headers=headers)
    assert staff_delete.status_code == status.HTTP_200_OK, staff_delete.text
    assert staff_delete.json()["data"]["status"] == "terminated"

    dept_delete = client.delete(f"/api/v1/admin/departments/{department_id}", headers=headers)
    assert dept_delete.status_code == status.HTTP_200_OK, dept_delete.text
    assert dept_delete.json()["data"]["is_active"] is False

    assert client.get(f"/api/v1/doctors/{doctor_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/staff/{staff_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/admin/departments/{department_id}", headers=headers).status_code == 404
