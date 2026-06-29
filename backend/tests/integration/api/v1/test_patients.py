"""Integration tests — MVP-072 patient CRUD API."""

from __future__ import annotations

import uuid
from datetime import date, datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"pat-{tenant_id.hex[:8]}@example.com"
    slug = f"pat-{tenant_id.hex[:8]}"

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
        data["location_id"] = location.id
        db.commit()

    yield data


@pytest.fixture
def hospital_admin_user():
    tenant_id = uuid.uuid4()
    email = f"pat-admin-{tenant_id.hex[:8]}@example.com"
    slug = f"pat-admin-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        db.commit()

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


def _patient_payload(**overrides: object) -> dict:
    payload = {
        "first_name": "Anita",
        "last_name": "Sharma",
        "date_of_birth": "1985-03-15",
        "gender": "female",
        "phone": "9876543210",
        "email": "anita@example.com",
        "blood_group": "B+",
        "address_line1": "123 MG Road",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        **CONSENT_DEFAULTS,
    }
    payload.update(overrides)
    return payload


def test_create_list_and_get_patient(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    payload = _patient_payload(location_id=str(receptionist_user["location_id"]))

    create = client.post("/api/v1/patients", json=payload, headers=headers)
    assert create.status_code == status.HTTP_201_CREATED
    created = create.json()["data"]
    assert created["first_name"] == "Anita"
    assert created["mrn"].startswith(f"MRN-{datetime.now().year}-")
    assert created["allergies"] == []
    assert created["contacts"] == []
    patient_id = created["id"]

    listing = client.get("/api/v1/patients", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert any(item["id"] == patient_id for item in listing.json()["data"])
    assert listing.json()["meta"]["pagination"]["total_items"] >= 1

    detail = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert detail.status_code == status.HTTP_200_OK
    assert detail.json()["data"]["phone"] == "9876543210"
    assert detail.json()["data"]["mrn"] == created["mrn"]

    with session_scope() as db:
        from sqlalchemy import select

        from app.models.audit.audit_log import AuditLog

        set_rls_tenant_context(db, receptionist_user["tenant_id"])
        audit_row = db.scalars(
            select(AuditLog).where(
                AuditLog.entity_type == "patient",
                AuditLog.entity_id == uuid.UUID(patient_id),
                AuditLog.action == "view",
            )
        ).first()
        assert audit_row is not None
        assert audit_row.audit_metadata is not None
        assert audit_row.audit_metadata.get("phi_access") is True


def test_update_patient(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    create = client.post("/api/v1/patients", json=_patient_payload(), headers=headers)
    patient_id = create.json()["data"]["id"]
    original_mrn = create.json()["data"]["mrn"]

    update = client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"city": "Pune", "occupation": "Teacher"},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    data = update.json()["data"]
    assert data["city"] == "Pune"
    assert data["occupation"] == "Teacher"
    assert data["mrn"] == original_mrn


def test_soft_delete_patient(client: TestClient, hospital_admin_user: dict) -> None:
    headers = _auth_headers(client, hospital_admin_user["slug"], hospital_admin_user["email"])
    create = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9123456780"),
        headers=headers,
    )
    patient_id = create.json()["data"]["id"]

    deleted = client.delete(f"/api/v1/patients/{patient_id}", headers=headers)
    assert deleted.status_code == status.HTTP_204_NO_CONTENT

    detail = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_search_patients_by_name_phone_and_mrn(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    create = client.post(
        "/api/v1/patients",
        json=_patient_payload(first_name="Ravi", last_name="Kumar", phone="9111222333"),
        headers=headers,
    )
    mrn = create.json()["data"]["mrn"]

    by_name = client.get("/api/v1/patients", params={"search": "Ravi"}, headers=headers)
    assert by_name.status_code == status.HTTP_200_OK
    assert any(item["mrn"] == mrn for item in by_name.json()["data"])

    by_phone = client.get("/api/v1/patients", params={"search": "9111222333"}, headers=headers)
    assert by_phone.status_code == status.HTTP_200_OK
    assert any(item["mrn"] == mrn for item in by_phone.json()["data"])

    by_mrn = client.get("/api/v1/patients", params={"search": mrn}, headers=headers)
    assert by_mrn.status_code == status.HTTP_200_OK
    assert any(item["mrn"] == mrn for item in by_mrn.json()["data"])


def test_duplicate_phone_returns_conflict(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    payload = _patient_payload(phone="9887766554")
    assert client.post("/api/v1/patients", json=payload, headers=headers).status_code == 201

    dup = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9887766554", first_name="Other"),
        headers=headers,
    )
    assert dup.status_code == status.HTTP_409_CONFLICT


def test_validation_rejects_future_dob(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    resp = client.post(
        "/api/v1/patients",
        json=_patient_payload(
            date_of_birth=str(date.today().replace(year=date.today().year + 1)),
            phone="9776655443",
        ),
        headers=headers,
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_search_min_length_validation(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    resp = client.get("/api/v1/patients", params={"search": "a"}, headers=headers)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_receptionist_cannot_delete_patient(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    create = client.post(
        "/api/v1/patients",
        json=_patient_payload(phone="9665544332"),
        headers=headers,
    )
    patient_id = create.json()["data"]["id"]
    assert client.delete(f"/api/v1/patients/{patient_id}", headers=headers).status_code == 403


def test_tenant_cannot_access_other_tenant_patient(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"pat-a-{suffix_a}"
    slug_b = f"pat-b-{suffix_b}"
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
        set_rls_tenant_context(db, data_b["tenant_id"])
        patient_b = PatientRepository(db, data_b["tenant_id"]).create(
            mrn="MRN-TEST-00001",
            first_name="Secret",
            date_of_birth=date(1990, 1, 1),
            gender="male",
            phone="9554433221",
        )
        db.commit()
        patient_b_id = patient_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    assert client.get(f"/api/v1/patients/{patient_b_id}", headers=headers_a).status_code == 404

    headers_b = _auth_headers(client, slug_b, email_b)
    assert client.get(f"/api/v1/patients/{patient_b_id}", headers=headers_b).status_code == 200


def test_doctor_can_read_but_not_create_without_permission(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"pat-doc-{suffix}"
    email = f"doc-{suffix}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="doctor",
        )

    headers = _auth_headers(client, slug, email)
    assert client.get("/api/v1/patients", headers=headers).status_code == 200
    assert (
        client.post("/api/v1/patients", json=_patient_payload(phone="9443322110"), headers=headers).status_code
        == 403
    )
