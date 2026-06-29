"""Integration tests — MVP-075 patient visit history API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.patients.repositories.visit_history_repository import PatientVisitHistoryRepository
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"visits-{tenant_id.hex[:8]}@example.com"
    slug = f"visits-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
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


def _create_patient(client: TestClient, headers: dict[str, str], phone: str) -> str:
    resp = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Anita",
            "last_name": "Sharma",
            "date_of_birth": "1990-01-01",
            "gender": "female",
            "phone": phone,
            **CONSENT_DEFAULTS,
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["data"]["id"]


def test_visit_history_empty_before_opd_tables(
    client: TestClient, receptionist_user: dict
) -> None:
    """Before Sprint 9 OPD migrations, visit history returns an empty paginated list."""
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876520001")

    with session_scope() as db:
        repo = PatientVisitHistoryRepository(db, receptionist_user["tenant_id"])
        assert repo.opd_visits_available() is False

    resp = client.get(f"/api/v1/patients/{patient_id}/visits", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["data"] == []
    assert body["meta"]["pagination"]["total_items"] == 0


def test_visit_history_patient_not_found(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    missing_id = uuid.uuid4()
    resp = client.get(f"/api/v1/patients/{missing_id}/visits", headers=headers)
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_visit_history_cross_tenant_returns_not_found(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"vis-a-{suffix_a}"
    slug_b = f"vis-b-{suffix_b}"
    email_a = f"a-{suffix_a}@example.com"
    email_b = f"b-{suffix_b}@example.com"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug_a,
            email=email_a,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        data_b = provision_tenant_with_role(
            db,
            slug=slug_b,
            email=email_b,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        set_rls_tenant_context(db, data_b["tenant_id"])
        patient_b = PatientRepository(db, data_b["tenant_id"]).create(
            mrn="MRN-VIS-00001",
            first_name="Hidden",
            date_of_birth=date(1990, 1, 1),
            gender="male",
            phone="9876520099",
        )
        db.commit()
        patient_b_id = patient_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    assert client.get(f"/api/v1/patients/{patient_b_id}/visits", headers=headers_a).status_code == 404


def test_doctor_can_read_visit_history(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"vis-doc-{suffix}"
    email_recv = f"recv-{suffix}@example.com"
    email_doc = f"doc-{suffix}@example.com"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email_recv,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        from app.domains.identity.services.rbac_service import RbacProvisioner
        from app.models.core.user import User

        doctor = User(
            tenant_id=data["tenant_id"],
            email=email_doc,
            password_hash=hash_password("SecurePass@123"),
            first_name="Doc",
            last_name="Tor",
            status="active",
        )
        db.add(doctor)
        db.flush()
        RbacProvisioner(db).assign_role(data["tenant_id"], doctor.id, "doctor")
        db.commit()

    recv_headers = _auth_headers(client, slug, email_recv)
    patient_id = _create_patient(client, recv_headers, "9876520010")

    doc_headers = _auth_headers(client, slug, email_doc)
    resp = client.get(f"/api/v1/patients/{patient_id}/visits", headers=doc_headers)
    assert resp.status_code == status.HTTP_200_OK
