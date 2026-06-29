"""Shared helpers for appointment API integration tests."""

from __future__ import annotations

import uuid
from datetime import date, time, timedelta
from decimal import Decimal

from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


def auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def patient_payload(**overrides: object) -> dict:
    payload = {
        "first_name": "Anita",
        "last_name": "Sharma",
        "date_of_birth": "1985-03-15",
        "gender": "female",
        "phone": "9876543210",
        **CONSENT_DEFAULTS,
    }
    payload.update(overrides)
    return payload


def appointment_payload(
    *,
    patient_id: str,
    doctor_id: str,
    location_id: str | None = None,
    appointment_date: str | None = None,
    **overrides: object,
) -> dict:
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date or (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00:00",
        "end_time": "09:20:00",
        "appointment_type": "new",
    }
    if location_id is not None:
        payload["location_id"] = location_id
    payload.update(overrides)
    return payload


def create_patient(client: TestClient, headers: dict[str, str], **overrides: object) -> str:
    response = client.post("/api/v1/patients", json=patient_payload(**overrides), headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["data"]["id"]


def create_appointment(
    client: TestClient,
    headers: dict[str, str],
    *,
    patient_id: str,
    doctor_id: str,
    **overrides: object,
) -> dict:
    response = client.post(
        "/api/v1/appointments",
        json=appointment_payload(patient_id=patient_id, doctor_id=doctor_id, **overrides),
        headers=headers,
    )
    return response


def provision_receptionist_with_doctor() -> dict:
    tenant_id = uuid.uuid4()
    email = f"appt-{tenant_id.hex[:8]}@example.com"
    slug = f"appt-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        location = LocationRepository(db, data["tenant_id"]).get_primary()
        assert location is not None
        dept = DepartmentRepository(db, data["tenant_id"]).create(
            name="General Medicine",
            code="GEN",
            location_id=location.id,
            is_active=True,
        )
        staff = StaffRepository(db, data["tenant_id"]).create(
            employee_code="DOC-001",
            first_name="Vikram",
            last_name="Patel",
            joining_date=date(2018, 1, 1),
            status="active",
            department_id=dept.id,
            location_id=location.id,
        )
        db.flush()
        doctor = DoctorRepository(db, data["tenant_id"]).create(
            staff_id=staff.id,
            specialization="General Medicine",
            consultation_fee=Decimal("500.00"),
            department_id=dept.id,
        )
        db.flush()
        schedule_repo = DoctorScheduleRepository(db, data["tenant_id"])
        for day in range(7):
            schedule_repo.create(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(8, 0),
                end_time=time(18, 0),
                slot_duration_minutes=20,
                max_patients_per_slot=1,
                location_id=location.id,
                is_active=True,
            )
        db.commit()
        data["location_id"] = location.id
        data["doctor_id"] = doctor.id

    return data


def assert_conflict_response(response, *, field: str = "start_time") -> None:
    assert response.status_code == status.HTTP_409_CONFLICT
    body = response.json()
    assert body["errors"][0]["code"] == "conflict"
    assert body["errors"][0]["field"] == field
    assert "booked" in body["errors"][0]["message"].lower()
