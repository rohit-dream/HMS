"""MVP-052 — OPD OpenAPI router stub integration tests."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration

OPD_STUB_ENDPOINTS: tuple[tuple[str, str, str], ...] = ()


@pytest.fixture
def opd_authorized_user():
    """Tenant with hospital_owner — has *:* for all OPD stub permission checks."""
    tenant_id = uuid.uuid4()
    email = f"opd-owner-{tenant_id.hex[:8]}@example.com"
    slug = f"opd-owner-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_owner",
        )

    yield data


@pytest.fixture
def receptionist_user():
    tenant_id = uuid.uuid4()
    email = f"opd-recv-{tenant_id.hex[:8]}@example.com"
    slug = f"opd-recv-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

    yield data


def _login(client: TestClient, slug: str, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass@123"},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    return resp.json()["data"]["access_token"]


def _auth_headers(slug: str, token: str) -> dict[str, str]:
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _minimal_body(method: str, path: str) -> dict | None:
    visit_id = str(uuid.uuid4())
    if method == "POST" and path.endswith("/visits"):
        return {
            "patient_id": str(uuid.uuid4()),
            "doctor_id": str(uuid.uuid4()),
            "visit_type": "walk_in",
        }
    if method == "POST" and path.endswith("/cancel"):
        return {"reason": "Patient left"}
    if method == "POST" and path.endswith("/skip"):
        return {"reason": "No show"}
    if method == "POST" and path.endswith("/queue"):
        return {"opd_visit_id": visit_id}
    if method == "POST" and path.endswith("/vitals"):
        return {"pulse_rate": 80}
    if method == "POST" and path.endswith("/notes"):
        return {"note_type": "general", "content": "Stub note"}
    if method == "POST" and path.endswith("/prescriptions"):
        return {
            "items": [
                {
                    "medicine_name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "twice daily",
                    "duration": "5 days",
                }
            ]
        }
    if method in {"PATCH"}:
        return {"chief_complaint": "Updated"} if "visits" in path else {"priority": "urgent"}
    if method == "GET" and path.endswith("/queue"):
        return None
    return {} if method in {"POST", "PATCH"} else None


@pytest.mark.parametrize("method,path,permission", OPD_STUB_ENDPOINTS)
def test_opd_stub_returns_501_for_authorized_admin(
    client: TestClient,
    opd_authorized_user: dict,
    method: str,
    path: str,
    permission: str,
) -> None:
    token = _login(client, opd_authorized_user["slug"], opd_authorized_user["email"])
    headers = _auth_headers(opd_authorized_user["slug"], token)
    body = _minimal_body(method, path)
    params = {"doctor_id": str(uuid.uuid4())} if path.endswith("/queue") and method == "GET" else None

    if method == "GET":
        resp = client.get(path, headers=headers, params=params)
    elif method == "POST":
        resp = client.post(path, json=body, headers=headers, params=params)
    elif method == "PATCH":
        resp = client.patch(path, json=body, headers=headers)
    else:
        pytest.fail(f"Unsupported method {method}")

    assert resp.status_code == status.HTTP_501_NOT_IMPLEMENTED, resp.text
    assert resp.json()["errors"][0]["code"] == "not_implemented"


def test_opd_endpoints_require_authentication(client: TestClient) -> None:
    resp = client.get("/api/v1/opd/visits")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_receptionist_denied_opd_consult_start(
    client: TestClient,
    receptionist_user: dict,
) -> None:
    token = _login(client, receptionist_user["slug"], receptionist_user["email"])
    headers = _auth_headers(receptionist_user["slug"], token)
    visit_id = uuid.uuid4()

    resp = client.post(
        f"/api/v1/opd/visits/{visit_id}/start",
        json={},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_receptionist_can_access_opd_queue_read(
    client: TestClient,
    receptionist_user: dict,
) -> None:
    token = _login(client, receptionist_user["slug"], receptionist_user["email"])
    headers = _auth_headers(receptionist_user["slug"], token)

    resp = client.get(
        "/api/v1/opd/queue",
        headers=headers,
        params={"doctor_id": str(uuid.uuid4()), "date": date.today().isoformat()},
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json()["errors"][0]["field"] == "doctor_id"


def test_opd_routes_registered_in_openapi(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json")
    assert schema.status_code == status.HTTP_200_OK
    paths = schema.json()["paths"]
    assert "/api/v1/opd/visits" in paths
    assert "/api/v1/opd/queue" in paths
    assert any("/api/v1/opd/visits/{visit_id}/vitals" in p for p in paths)
    assert any("/api/v1/opd/visits/{visit_id}/prescriptions" in p for p in paths)

    opd_paths = [p for p in paths if p.startswith("/api/v1/opd/")]
    assert len(opd_paths) >= 14

    opd_operations = sum(len(paths[p]) for p in opd_paths)
    assert opd_operations >= 20

    tags = {tag for path in opd_paths for method in paths[path] for tag in paths[path][method].get("tags", [])}
    assert "OPD" in tags
