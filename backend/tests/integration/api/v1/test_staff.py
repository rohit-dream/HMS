"""Integration tests — MVP-061 staff API."""

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
from app.domains.org.repositories.staff_repository import StaffRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def hospital_admin_user():
    tenant_id = uuid.uuid4()
    email = f"staff-{tenant_id.hex[:8]}@example.com"
    slug = f"staff-{tenant_id.hex[:8]}"

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
        db.commit()
        data["location_id"] = location.id
        data["department_id"] = dept.id

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


def test_create_list_and_get_staff(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    payload = {
        "employee_code": "emp-001",
        "first_name": "Vikram",
        "last_name": "Patel",
        "email": "vikram@example.com",
        "department_id": str(hospital_admin_user["department_id"]),
        "designation": "Consultant",
        "joining_date": "2020-01-15",
        "location_id": str(hospital_admin_user["location_id"]),
    }

    create = client.post("/api/v1/staff", json=payload, headers=headers)
    assert create.status_code == status.HTTP_201_CREATED
    created = create.json()["data"]
    assert created["employee_code"] == "EMP-001"
    assert created["department_name"] == "General Medicine"
    assert created["status"] == "active"
    assert created["is_doctor"] is False
    staff_id = created["id"]

    listing = client.get("/api/v1/staff", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == staff_id for item in listing.json()["data"])

    detail = client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["first_name"] == "Vikram"


def test_update_staff_and_link_user(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/staff",
        json={
            "employee_code": "EMP-002",
            "first_name": "Sunita",
            "last_name": "Nair",
            "joining_date": "2024-06-01",
        },
        headers=headers,
    )
    staff_id = create.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/staff/{staff_id}",
        json={
            "designation": "Billing Executive",
            "status": "on_leave",
            "user_id": str(hospital_admin_user["user_id"]),
        },
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    data = update.json()["data"]
    assert data["designation"] == "Billing Executive"
    assert data["status"] == "on_leave"
    assert data["user_id"] == str(hospital_admin_user["user_id"])


def test_duplicate_employee_code_returns_conflict(
    client: TestClient, hospital_admin_user: dict
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    payload = {
        "employee_code": "EMP-DUP",
        "first_name": "A",
        "last_name": "B",
        "joining_date": "2024-01-01",
    }
    assert client.post("/api/v1/staff", json=payload, headers=headers).status_code == 201
    dup = client.post("/api/v1/staff", json=payload, headers=headers)
    assert dup.status_code == status.HTTP_409_CONFLICT


def test_soft_delete_staff(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/staff",
        json={
            "employee_code": "EMP-TMP",
            "first_name": "Temp",
            "last_name": "Staff",
            "joining_date": str(date.today()),
        },
        headers=headers,
    )
    staff_id = create.json()["data"]["id"]

    deleted = client.delete(f"/api/v1/staff/{staff_id}", headers=headers)
    assert deleted.status_code == status.HTTP_200_OK
    assert deleted.json()["data"]["status"] == "terminated"

    detail = client.get(f"/api/v1/staff/{staff_id}", headers=headers)
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_staff_api_requires_permission(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"staff-recv-{suffix}"
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
    resp = client.get("/api/v1/staff", headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_tenant_cannot_access_other_tenant_staff(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"staff-a-{suffix_a}"
    slug_b = f"staff-b-{suffix_b}"
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
            employee_code="SECRET",
            first_name="Secret",
            last_name="Employee",
            joining_date=date.today(),
            status="active",
        )
        db.commit()
        staff_b_id = staff_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    assert client.get(f"/api/v1/staff/{staff_b_id}", headers=headers_a).status_code == 404

    headers_b = _auth_headers(client, slug_b, email_b)
    assert client.get(f"/api/v1/staff/{staff_b_id}", headers=headers_b).status_code == 200
