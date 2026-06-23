"""Integration tests — MVP-060 departments API."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def hospital_admin_user():
    tenant_id = uuid.uuid4()
    email = f"dept-{tenant_id.hex[:8]}@example.com"
    slug = f"dept-{tenant_id.hex[:8]}"

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
        data["location_id"] = location.id

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


def test_create_list_and_get_department(
    client: TestClient, hospital_admin_user: dict
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    payload = {
        "name": "Cardiology",
        "code": "card",
        "location_id": str(hospital_admin_user["location_id"]),
    }

    create = client.post("/api/v1/admin/departments", json=payload, headers=headers)
    assert create.status_code == status.HTTP_201_CREATED
    created = create.json()["data"]
    assert created["name"] == "Cardiology"
    assert created["code"] == "CARD"
    assert created["is_active"] is True
    department_id = created["id"]

    listing = client.get("/api/v1/admin/departments", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    items = listing.json()["data"]
    assert any(item["id"] == department_id for item in items)

    detail = client.get(f"/api/v1/admin/departments/{department_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["code"] == "CARD"


def test_update_department(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/admin/departments",
        json={"name": "Radiology", "code": "RAD"},
        headers=headers,
    )
    department_id = create.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/admin/departments/{department_id}",
        json={"name": "Diagnostic Radiology", "is_active": False},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    data = update.json()["data"]
    assert data["name"] == "Diagnostic Radiology"
    assert data["is_active"] is False


def test_duplicate_department_code_returns_conflict(
    client: TestClient, hospital_admin_user: dict
) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    first = client.post(
        "/api/v1/admin/departments",
        json={"name": "OPD", "code": "OPD"},
        headers=headers,
    )
    assert first.status_code == status.HTTP_201_CREATED

    second = client.post(
        "/api/v1/admin/departments",
        json={"name": "Outpatient", "code": "opd"},
        headers=headers,
    )
    assert second.status_code == status.HTTP_409_CONFLICT
    assert second.json()["errors"][0]["code"] == "conflict"


def test_soft_delete_department(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/admin/departments",
        json={"name": "Temp Dept", "code": "TMP"},
        headers=headers,
    )
    department_id = create.json()["data"]["id"]

    deleted = client.delete(f"/api/v1/admin/departments/{department_id}", headers=headers)
    assert deleted.status_code == status.HTTP_200_OK

    detail = client.get(f"/api/v1/admin/departments/{department_id}", headers=headers)
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_department_api_requires_permission(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"dept-recv-{suffix}"
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
    resp = client.get("/api/v1/admin/departments", headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_tenant_cannot_access_other_tenant_department(
    client: TestClient,
) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"dept-a-{suffix_a}"
    slug_b = f"dept-b-{suffix_b}"
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
        dept_b = DepartmentRepository(db, data_b["tenant_id"]).create(
            name="Tenant B Secret",
            code="SECRET",
            is_active=True,
        )
        db.commit()
        dept_b_id = dept_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    resp = client.get(f"/api/v1/admin/departments/{dept_b_id}", headers=headers_a)
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    headers_b = _auth_headers(client, slug_b, email_b)
    ok = client.get(f"/api/v1/admin/departments/{dept_b_id}", headers=headers_b)
    assert ok.status_code == status.HTTP_200_OK
