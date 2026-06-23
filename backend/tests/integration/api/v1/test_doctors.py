"""Integration tests — MVP-062 doctors API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def hospital_admin_user():
    tenant_id = uuid.uuid4()
    email = f"doc-{tenant_id.hex[:8]}@example.com"
    slug = f"doc-{tenant_id.hex[:8]}"

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
            employee_code="DOC-001",
            first_name="Vikram",
            last_name="Patel",
            joining_date=date(2018, 1, 1),
            status="active",
            department_id=dept.id,
            location_id=location.id,
        )
        db.commit()
        data["location_id"] = location.id
        data["department_id"] = dept.id
        data["staff_id"] = staff.id

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


def test_create_list_and_get_doctor(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    payload = {
        "staff_id": str(hospital_admin_user["staff_id"]),
        "specialization": "General Medicine",
        "qualification": "MBBS, MD",
        "consultation_fee": "500.00",
        "follow_up_fee": "300.00",
        "department_id": str(hospital_admin_user["department_id"]),
        "registration_number": "MH-12345",
    }

    create = client.post("/api/v1/doctors", json=payload, headers=headers)
    assert create.status_code == status.HTTP_201_CREATED
    created = create.json()["data"]
    assert created["first_name"] == "Vikram"
    assert created["specialization"] == "General Medicine"
    assert created["department_name"] == "General Medicine"
    doctor_id = created["id"]

    listing = client.get("/api/v1/doctors", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == doctor_id for item in listing.json()["data"])

    detail = client.get(f"/api/v1/doctors/{doctor_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["registration_number"] == "MH-12345"


def test_update_doctor(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/doctors",
        json={
            "staff_id": str(hospital_admin_user["staff_id"]),
            "specialization": "Pediatrics",
            "consultation_fee": "750.00",
        },
        headers=headers,
    )
    doctor_id = create.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/doctors/{doctor_id}",
        json={"is_available": False, "consultation_fee": "800.00"},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    data = update.json()["data"]
    assert data["is_available"] is False
    assert data["consultation_fee"] == "800.00"


def test_duplicate_staff_doctor_returns_conflict(
    client: TestClient, hospital_admin_user: dict
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    payload = {
        "staff_id": str(hospital_admin_user["staff_id"]),
        "specialization": "General Medicine",
        "consultation_fee": "500.00",
    }
    assert client.post("/api/v1/doctors", json=payload, headers=headers).status_code == 201
    dup = client.post("/api/v1/doctors", json=payload, headers=headers)
    assert dup.status_code == status.HTTP_409_CONFLICT


def test_soft_delete_doctor(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/doctors",
        json={
            "staff_id": str(hospital_admin_user["staff_id"]),
            "specialization": "Dermatology",
            "consultation_fee": "600.00",
        },
        headers=headers,
    )
    doctor_id = create.json()["data"]["id"]

    deleted = client.delete(f"/api/v1/doctors/{doctor_id}", headers=headers)
    assert deleted.status_code == status.HTTP_200_OK
    assert deleted.json()["data"]["is_available"] is False

    detail = client.get(f"/api/v1/doctors/{doctor_id}", headers=headers)
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_receptionist_can_list_doctors(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"doc-recv-{suffix}"
    email = f"recv-{suffix}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

    headers = _auth_headers(client, slug, email)
    resp = client.get("/api/v1/doctors", headers=headers)
    assert resp.status_code == status.HTTP_200_OK


def test_receptionist_cannot_create_doctor(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"doc-recv2-{suffix}"
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
        "/api/v1/doctors",
        json={
            "staff_id": str(uuid.uuid4()),
            "specialization": "X",
            "consultation_fee": "100.00",
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_tenant_cannot_access_other_tenant_doctor(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"doc-a-{suffix_a}"
    slug_b = f"doc-b-{suffix_b}"
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
            employee_code="DOC-SECRET",
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
        db.commit()
        doctor_b_id = doctor_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    assert client.get(f"/api/v1/doctors/{doctor_b_id}", headers=headers_a).status_code == 404

    headers_b = _auth_headers(client, slug_b, email_b)
    assert client.get(f"/api/v1/doctors/{doctor_b_id}", headers=headers_b).status_code == 200
