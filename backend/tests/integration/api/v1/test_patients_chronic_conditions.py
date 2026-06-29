"""Integration tests — MVP-074 patient chronic conditions API."""

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
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"chronic-{tenant_id.hex[:8]}@example.com"
    slug = f"chronic-{tenant_id.hex[:8]}"

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


def test_add_and_list_chronic_conditions(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876510001")

    create = client.post(
        f"/api/v1/patients/{patient_id}/chronic-conditions",
        json={
            "condition_name": "Type 2 Diabetes",
            "icd_code": "E11",
            "diagnosed_date": "2015-03-01",
            "status": "active",
            "notes": "On metformin",
        },
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED
    condition = create.json()["data"]
    assert condition["condition_name"] == "Type 2 Diabetes"
    assert condition["status"] == "active"
    assert "id" in condition
    assert "recorded_at" in condition

    listing = client.get(
        f"/api/v1/patients/{patient_id}/chronic-conditions",
        headers=headers,
    )
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.json()["data"]) == 1

    profile = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert profile.status_code == status.HTTP_200_OK
    assert len(profile.json()["data"]["chronic_conditions"]) == 1


def test_duplicate_active_chronic_condition_returns_conflict(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876510002")

    payload = {"condition_name": "Hypertension", "status": "active"}
    assert (
        client.post(
            f"/api/v1/patients/{patient_id}/chronic-conditions",
            json=payload,
            headers=headers,
        ).status_code
        == 201
    )

    dup = client.post(
        f"/api/v1/patients/{patient_id}/chronic-conditions",
        json=payload,
        headers=headers,
    )
    assert dup.status_code == status.HTTP_409_CONFLICT


def test_resolved_condition_allows_same_name_reentry(
    client: TestClient, receptionist_user: dict
) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876510003")

    client.post(
        f"/api/v1/patients/{patient_id}/chronic-conditions",
        json={"condition_name": "Asthma", "status": "resolved"},
        headers=headers,
    )
    create = client.post(
        f"/api/v1/patients/{patient_id}/chronic-conditions",
        json={"condition_name": "Asthma", "status": "active"},
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED


def test_cross_tenant_chronic_conditions_not_visible(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"chr-a-{suffix_a}"
    slug_b = f"chr-b-{suffix_b}"
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
            mrn="MRN-CHR-00001",
            first_name="Hidden",
            date_of_birth=date(1990, 1, 1),
            gender="male",
            phone="9876510099",
            chronic_conditions=[
                {
                    "id": str(uuid.uuid4()),
                    "condition_name": "Secret Condition",
                    "status": "active",
                    "recorded_at": "2026-01-01T00:00:00+00:00",
                }
            ],
        )
        db.commit()
        patient_b_id = patient_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    assert (
        client.get(f"/api/v1/patients/{patient_b_id}/chronic-conditions", headers=headers_a).status_code
        == 404
    )
