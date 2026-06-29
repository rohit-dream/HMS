"""
MVP-082 — Patient management end-to-end integration workflow (Sprint 7).

Exercises registration, profile sub-resources, search, duplicate check, and visit history.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.patient import minimal_patient_payload
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK, resp.text
    token = resp.json()["data"]["access_token"]
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def test_patient_lifecycle_workflow_e2e(client: TestClient) -> None:
    """Full Sprint 7 patient slice — register, enrich profile, search, duplicate warning."""
    suffix = uuid.uuid4().hex[:8]
    slug = f"pat-e2e-{suffix}"
    email = f"pat-e2e-{suffix}@example.com"
    phone = f"98765{int(suffix, 16) % 100000:05d}"

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
        location_id = location.id

    headers = _auth_headers(client, slug, email)

    create = client.post(
        "/api/v1/patients",
        json=minimal_patient_payload(
            phone=phone,
            location_id=str(location_id),
            consent_method="written",
        ),
        headers=headers,
    )
    assert create.status_code == status.HTTP_201_CREATED, create.text
    patient = create.json()["data"]
    patient_id = patient["id"]
    mrn = patient["mrn"]
    assert patient["consent_method"] == "written"
    assert patient["consent_given_at"] is not None

    allergy = client.post(
        f"/api/v1/patients/{patient_id}/allergies",
        json={
            "allergen": "Penicillin",
            "severity": "severe",
            "reaction": "Rash",
            "onset_date": "2015-01-01",
        },
        headers=headers,
    )
    assert allergy.status_code == status.HTTP_201_CREATED, allergy.text

    contact = client.post(
        f"/api/v1/patients/{patient_id}/contacts",
        json={
            "name": "Raj Sharma",
            "relationship": "spouse",
            "phone": "9123456780",
            "is_emergency": True,
            "is_primary": True,
        },
        headers=headers,
    )
    assert contact.status_code == status.HTTP_201_CREATED, contact.text

    condition = client.post(
        f"/api/v1/patients/{patient_id}/chronic-conditions",
        json={
            "condition_name": "Hypertension",
            "icd_code": "I10",
            "status": "active",
        },
        headers=headers,
    )
    assert condition.status_code == status.HTTP_201_CREATED, condition.text

    profile = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert profile.status_code == status.HTTP_200_OK
    body = profile.json()["data"]
    assert len(body["allergies"]) == 1
    assert len(body["contacts"]) == 1
    assert len(body["chronic_conditions"]) == 1

    by_phone = client.get("/api/v1/patients", params={"search": phone}, headers=headers)
    assert by_phone.status_code == status.HTTP_200_OK
    assert any(item["id"] == patient_id for item in by_phone.json()["data"])

    by_mrn = client.get("/api/v1/patients", params={"search": mrn}, headers=headers)
    assert by_mrn.status_code == status.HTTP_200_OK
    assert any(item["mrn"] == mrn for item in by_mrn.json()["data"])

    duplicate = client.get(
        "/api/v1/patients/check-duplicate",
        params={"phone": phone},
        headers=headers,
    )
    assert duplicate.status_code == status.HTTP_200_OK
    assert duplicate.json()["data"]["has_duplicates"] is True

    visits = client.get(f"/api/v1/patients/{patient_id}/visits", headers=headers)
    assert visits.status_code == status.HTTP_200_OK
    assert visits.json()["data"] == []

    update = client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"occupation": "Teacher"},
        headers=headers,
    )
    assert update.status_code == status.HTTP_200_OK
    assert update.json()["data"]["occupation"] == "Teacher"
