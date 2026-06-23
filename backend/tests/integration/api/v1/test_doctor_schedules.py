"""Integration tests — MVP-063 doctor schedules API."""

from __future__ import annotations

import uuid
from datetime import date, time

import pytest
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
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def doctor_context():
    tenant_id = uuid.uuid4()
    email = f"sch-{tenant_id.hex[:8]}@example.com"
    slug = f"sch-{tenant_id.hex[:8]}"

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
        dept = DepartmentRepository(db, data["tenant_id"]).create(
            name="General Medicine",
            code="GEN",
            location_id=location.id,
            is_active=True,
        )
        staff = StaffRepository(db, data["tenant_id"]).create(
            employee_code="DOC-SCH-001",
            first_name="Anita",
            last_name="Desai",
            joining_date=date(2019, 3, 1),
            status="active",
            department_id=dept.id,
            location_id=location.id,
        )
        db.flush()
        doctor = DoctorRepository(db, data["tenant_id"]).create(
            staff_id=staff.id,
            specialization="General Medicine",
            consultation_fee=500,
            department_id=dept.id,
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


def _schedule_payload(**overrides: object) -> dict:
    payload = {
        "day_of_week": 1,
        "start_time": "09:00:00",
        "end_time": "13:00:00",
        "slot_duration_minutes": 20,
        "max_patients_per_slot": 1,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def test_create_list_and_get_schedule(client: TestClient, doctor_context: dict) -> None:
    headers = _auth_headers(client, doctor_context["slug"], doctor_context["email"])
    doctor_id = doctor_context["doctor_id"]
    base = f"/api/v1/doctors/{doctor_id}/schedules"

    create = client.post(base, json=_schedule_payload(), headers=headers)
    assert create.status_code == status.HTTP_201_CREATED
    created = create.json()["data"]
    assert created["day_of_week"] == 1
    assert created["start_time"] == "09:00:00"
    schedule_id = created["id"]

    listing = client.get(base, headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == schedule_id for item in listing.json()["data"])

    detail = client.get(f"{base}/{schedule_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["slot_duration_minutes"] == 20


def test_update_schedule(client: TestClient, doctor_context: dict) -> None:
    headers = _auth_headers(client, doctor_context["slug"], doctor_context["email"])
    doctor_id = doctor_context["doctor_id"]
    base = f"/api/v1/doctors/{doctor_id}/schedules"

    create = client.post(base, json=_schedule_payload(day_of_week=2), headers=headers)
    schedule_id = create.json()["data"]["id"]

    update = client.patch(
        f"{base}/{schedule_id}",
        json={"end_time": "14:00:00", "slot_duration_minutes": 30},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    data = update.json()["data"]
    assert data["end_time"] == "14:00:00"
    assert data["slot_duration_minutes"] == 30


def test_overlapping_schedule_returns_conflict(client: TestClient, doctor_context: dict) -> None:
    headers = _auth_headers(client, doctor_context["slug"], doctor_context["email"])
    doctor_id = doctor_context["doctor_id"]
    base = f"/api/v1/doctors/{doctor_id}/schedules"

    assert client.post(base, json=_schedule_payload(), headers=headers).status_code == 201
    overlap = client.post(
        base,
        json=_schedule_payload(start_time="11:00:00", end_time="15:00:00"),
        headers=headers,
    )
    assert overlap.status_code == status.HTTP_409_CONFLICT


def test_non_overlapping_same_day_allowed(client: TestClient, doctor_context: dict) -> None:
    headers = _auth_headers(client, doctor_context["slug"], doctor_context["email"])
    doctor_id = doctor_context["doctor_id"]
    base = f"/api/v1/doctors/{doctor_id}/schedules"

    assert client.post(
        base,
        json=_schedule_payload(start_time="09:00:00", end_time="12:00:00"),
        headers=headers,
    ).status_code == 201
    second = client.post(
        base,
        json=_schedule_payload(start_time="12:00:00", end_time="15:00:00"),
        headers=headers,
    )
    assert second.status_code == status.HTTP_201_CREATED


def test_soft_delete_schedule(client: TestClient, doctor_context: dict) -> None:
    headers = _auth_headers(client, doctor_context["slug"], doctor_context["email"])
    doctor_id = doctor_context["doctor_id"]
    base = f"/api/v1/doctors/{doctor_id}/schedules"

    create = client.post(base, json=_schedule_payload(day_of_week=3), headers=headers)
    schedule_id = create.json()["data"]["id"]

    deleted = client.delete(f"{base}/{schedule_id}", headers=headers)
    assert deleted.status_code == status.HTTP_200_OK
    assert deleted.json()["data"]["is_active"] is False

    detail = client.get(f"{base}/{schedule_id}", headers=headers)
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_receptionist_can_list_schedules(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"sch-recv-{suffix}"
    email = f"recv-{suffix}@example.com"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        staff = StaffRepository(db, data["tenant_id"]).create(
            employee_code="DOC-RECV-001",
            first_name="Reception",
            last_name="Doctor",
            joining_date=date.today(),
            status="active",
        )
        db.flush()
        doctor = DoctorRepository(db, data["tenant_id"]).create(
            staff_id=staff.id,
            specialization="General Medicine",
            consultation_fee=400,
        )
        db.flush()
        DoctorScheduleRepository(db, data["tenant_id"]).create(
            doctor_id=doctor.id,
            day_of_week=4,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
        )
        db.commit()
        doctor_id = doctor.id

    headers = _auth_headers(client, slug, email)
    resp = client.get(f"/api/v1/doctors/{doctor_id}/schedules", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.json()["data"]) == 1


def test_receptionist_cannot_create_schedule(client: TestClient, doctor_context: dict) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"sch-recv2-{suffix}"
    email = f"recv2-{suffix}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

    headers = _auth_headers(client, slug, email)
    resp = client.post(
        f"/api/v1/doctors/{doctor_context['doctor_id']}/schedules",
        json=_schedule_payload(),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_tenant_cannot_access_other_tenant_schedule(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"sch-a-{suffix_a}"
    slug_b = f"sch-b-{suffix_b}"
    email_a = f"admin-a-{suffix_a}@example.com"
    email_b = f"admin-b-{suffix_b}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug_a,
            email=email_a,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        data_b = provision_tenant_with_role(
            db,
            slug=slug_b,
            email=email_b,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        staff_b = StaffRepository(db, data_b["tenant_id"]).create(
            employee_code="DOC-SECRET-SCH",
            first_name="Secret",
            last_name="Doctor",
            joining_date=date.today(),
            status="active",
        )
        db.flush()
        doctor_b = DoctorRepository(db, data_b["tenant_id"]).create(
            staff_id=staff_b.id,
            specialization="Hidden",
            consultation_fee=100,
        )
        db.flush()
        schedule_b = DoctorScheduleRepository(db, data_b["tenant_id"]).create(
            doctor_id=doctor_b.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration_minutes=20,
        )
        db.commit()
        doctor_b_id = doctor_b.id
        schedule_b_id = schedule_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    base = f"/api/v1/doctors/{doctor_b_id}/schedules"
    assert client.get(base, headers=headers_a).status_code == 404
    assert client.get(f"{base}/{schedule_b_id}", headers=headers_a).status_code == 404

    headers_b = _auth_headers(client, slug_b, email_b)
    assert client.get(base, headers=headers_b).status_code == 200
    assert client.get(f"{base}/{schedule_b_id}", headers=headers_b).status_code == 200
