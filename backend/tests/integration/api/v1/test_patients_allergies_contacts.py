"""Integration tests — MVP-073 patient allergies and contacts API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from app.domains.patients.repositories.patient_allergy_repository import PatientAllergyRepository
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.identity.services.rbac_service import RbacProvisioner
from app.models.core.user import User
from tests.helpers.patient import CONSENT_DEFAULTS
from tests.helpers.rbac import provision_tenant_with_role


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"allergy-{tenant_id.hex[:8]}@example.com"
    slug = f"allergy-{tenant_id.hex[:8]}"

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


def test_add_list_and_delete_allergy(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876500001")

    create = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        json={
            "allergen": "Penicillin",
            "severity": "severe",
            "reaction": "Anaphylaxis",
            "onset_date": "2010-05-01",
        },
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED
    allergy = create.json()["data"]
    assert allergy["allergen"] == "Penicillin"
    assert allergy["severity"] == "severe"
    allergy_id = allergy["id"]

    listing = client.get(f"/api/v1/patients/{patient_id}/allergies", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.json()["data"]) == 1

    profile = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert profile.status_code == status.HTTP_200_OK
    assert len(profile.json()["data"]["allergies"]) == 1

    deleted = client.delete(
        f"/api/v1/patients/{patient_id}/allergies/{allergy_id}",
        headers=headers,
    )
    assert deleted.status_code == status.HTTP_204_NO_CONTENT

    listing_after = client.get(f"/api/v1/patients/{patient_id}/allergies", headers=headers)
    assert listing_after.json()["data"] == []


def test_add_and_list_contacts(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876500002")

    create = client.post(
        f"/api/v1/patients/{patient_id}/contacts",
        json={
            "name": "Ravi Sharma",
            "relationship": "spouse",
            "phone": "9876500003",
            "email": "ravi@example.com",
            "is_emergency": True,
            "is_primary": True,
        },
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED
    contact = create.json()["data"]
    assert contact["is_primary"] is True
    assert contact["is_emergency"] is True

    listing = client.get(f"/api/v1/patients/{patient_id}/contacts", headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    assert len(listing.json()["data"]) == 1

    profile = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert len(profile.json()["data"]["contacts"]) == 1


def test_primary_contact_replaces_previous(client: TestClient, receptionist_user: dict) -> None:
    headers = _auth_headers(client, receptionist_user["slug"], receptionist_user["email"])
    patient_id = _create_patient(client, headers, "9876500004")

    client.post(
        f"/api/v1/patients/{patient_id}/contacts",
        json={
            "name": "First Contact",
            "relationship": "parent",
            "phone": "9876500005",
            "is_primary": True,
        },
        headers=headers,
    )
    client.post(
        f"/api/v1/patients/{patient_id}/contacts",
        json={
            "name": "Second Contact",
            "relationship": "spouse",
            "phone": "9876500006",
            "is_primary": True,
        },
        headers=headers,
    )

    listing = client.get(f"/api/v1/patients/{patient_id}/contacts", headers=headers)
    contacts = listing.json()["data"]
    primary_count = sum(1 for c in contacts if c["is_primary"])
    assert primary_count == 1
    assert any(c["name"] == "Second Contact" and c["is_primary"] for c in contacts)


def test_pharmacist_can_read_but_not_add_allergy(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:8]
    slug = f"allergy-pharm-{suffix}"
    email_recv = f"recv-{suffix}@example.com"
    email_pharm = f"pharm-{suffix}@example.com"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email_recv,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        pharmacist = User(
            tenant_id=data["tenant_id"],
            email=email_pharm,
            password_hash=hash_password("SecurePass@123"),
            first_name="Pharma",
            last_name="User",
            status="active",
        )
        db.add(pharmacist)
        db.flush()
        RbacProvisioner(db).assign_role(data["tenant_id"], pharmacist.id, "pharmacist")
        db.commit()

    recv_headers = _auth_headers(client, slug, email_recv)
    patient_id = _create_patient(client, recv_headers, "9876500008")

    pharm_headers = _auth_headers(client, slug, email_pharm)
    assert (
        client.get(f"/api/v1/patients/{patient_id}/allergies", headers=pharm_headers).status_code
        == status.HTTP_200_OK
    )
    assert (
        client.post(
            f"/api/v1/patients/{patient_id}/allergies",
            json={"allergen": "Latex", "severity": "mild"},
            headers=pharm_headers,
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )


def test_cross_tenant_allergy_not_visible(client: TestClient) -> None:
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"all-a-{suffix_a}"
    slug_b = f"all-b-{suffix_b}"
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
            mrn="MRN-X-00001",
            first_name="Hidden",
            date_of_birth=date(1990, 1, 1),
            gender="male",
            phone="9876500099",
        )
        db.flush()
        allergy_b = PatientAllergyRepository(db, data_b["tenant_id"]).create(
            patient_id=patient_b.id,
            allergen="Secret",
            severity="mild",
        )
        db.commit()
        patient_b_id = patient_b.id
        allergy_b_id = allergy_b.id

    headers_a = _auth_headers(client, slug_a, email_a)
    assert client.get(f"/api/v1/patients/{patient_b_id}/allergies", headers=headers_a).status_code == 404
    assert (
        client.delete(
            f"/api/v1/patients/{patient_b_id}/allergies/{allergy_b_id}",
            headers=headers_a,
        ).status_code
        == 404
    )
