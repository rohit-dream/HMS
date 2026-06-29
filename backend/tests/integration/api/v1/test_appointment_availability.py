"""Integration tests — MVP-085 appointment availability API."""

from __future__ import annotations

import uuid
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.clinical.availability_slots import schedule_day_of_week
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.doctor_schedule_repository import DoctorScheduleRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def booking_context():
    tenant_id = uuid.uuid4()
    email = f"avail-{tenant_id.hex[:8]}@example.com"
    slug = f"avail-{tenant_id.hex[:8]}"

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
            employee_code="DOC-AVL",
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
                start_time=time(9, 0),
                end_time=time(11, 0),
                slot_duration_minutes=20,
                max_patients_per_slot=1,
                location_id=location.id,
                is_active=True,
            )
        db.commit()
        data["location_id"] = location.id
        data["doctor_id"] = doctor.id

    yield data


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _next_weekday(target_day: int) -> date:
    """Return the next calendar date matching schedule day_of_week (0=Sunday)."""
    probe = date.today() + timedelta(days=1)
    while schedule_day_of_week(probe) != target_day:
        probe += timedelta(days=1)
    return probe


def test_availability_returns_schedule_slots(client: TestClient, booking_context: dict) -> None:
    headers = _auth_headers(client, booking_context["slug"], booking_context["email"])
    appt_date = _next_weekday(1)  # Monday

    resp = client.get(
        "/api/v1/appointments/availability",
        params={
            "doctor_id": str(booking_context["doctor_id"]),
            "date": appt_date.isoformat(),
            "location_id": str(booking_context["location_id"]),
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["doctor_id"] == str(booking_context["doctor_id"])
    assert data["date"] == appt_date.isoformat()
    assert len(data["slots"]) == 6
    assert data["slots"][0] == {
        "start_time": "09:00:00",
        "end_time": "09:20:00",
        "available": True,
    }


def test_availability_marks_booked_slot_unavailable(
    client: TestClient,
    booking_context: dict,
) -> None:
    headers = _auth_headers(client, booking_context["slug"], booking_context["email"])
    appt_date = _next_weekday(1)

    patient = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Anita",
            "last_name": "Sharma",
            "date_of_birth": "1985-03-15",
            "gender": "female",
            "phone": "9876543210",
            **CONSENT_DEFAULTS,
        },
        headers=headers,
    )
    patient_id = patient.json()["data"]["id"]
    book = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": str(booking_context["doctor_id"]),
            "location_id": str(booking_context["location_id"]),
            "appointment_date": appt_date.isoformat(),
            "start_time": "09:20:00",
            "end_time": "09:40:00",
            "appointment_type": "new",
        },
        headers=headers,
    )
    assert book.status_code == status.HTTP_201_CREATED

    resp = client.get(
        "/api/v1/appointments/availability",
        params={
            "doctor_id": str(booking_context["doctor_id"]),
            "date": appt_date.isoformat(),
        },
        headers=headers,
    )
    slots = {slot["start_time"]: slot for slot in resp.json()["data"]["slots"]}
    assert slots["09:00:00"]["available"] is True
    assert slots["09:20:00"]["available"] is False


def test_cannot_book_outside_doctor_schedule(
    client: TestClient,
    booking_context: dict,
) -> None:
    headers = _auth_headers(client, booking_context["slug"], booking_context["email"])
    appt_date = _next_weekday(1)
    patient_id = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Ravi",
            "last_name": "Kumar",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "phone": "9876543211",
            **CONSENT_DEFAULTS,
        },
        headers=headers,
    ).json()["data"]["id"]

    resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": patient_id,
            "doctor_id": str(booking_context["doctor_id"]),
            "appointment_date": appt_date.isoformat(),
            "start_time": "11:00:00",
            "end_time": "11:20:00",
            "appointment_type": "new",
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "outside the doctor schedule" in resp.json()["errors"][0]["message"]


def test_availability_requires_doctor_in_tenant(client: TestClient, booking_context: dict) -> None:
    other_tenant = uuid.uuid4()
    with session_scope() as db:
        other = provision_tenant_with_role(
            db,
            slug=f"other-{other_tenant.hex[:8]}",
            email=f"other-{other_tenant.hex[:8]}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        db.commit()

    headers = _auth_headers(client, other["slug"], other["email"])
    resp = client.get(
        "/api/v1/appointments/availability",
        params={
            "doctor_id": str(booking_context["doctor_id"]),
            "date": (date.today() + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
