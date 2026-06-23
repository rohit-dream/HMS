"""
MVP-050 — Gate G2 end-to-end platform admin workflow (Sprint 4).

Covers the Sprint 4 vertical slice:
register → login → hospital profile/settings → branch → invite → accept-invite → RBAC.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.domains.platform.constants import LEGAL_ACCEPTANCE_SETTING_KEY
from tests.helpers.auth import register_payload

pytestmark = pytest.mark.integration


def _auth_headers(slug: str, token: str) -> dict[str, str]:
    return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}


def _login(client: TestClient, slug: str, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK, resp.text
    return resp.json()["data"]["access_token"]


def test_g2_platform_admin_workflow_e2e(client: TestClient) -> None:
    """
    Gate G2 — full Sprint 4 platform path:
    legal versions → register → owner login → hospital admin → invite → accept → RBAC.
    """
    legal = client.get("/api/v1/platform/legal-versions")
    assert legal.status_code == status.HTTP_200_OK
    assert legal.json()["data"]["terms_version"]

    payload = register_payload()
    owner_password = payload["owner_password"]
    slug = payload["slug"]
    owner_email = payload["email"]

    register = client.post("/api/v1/platform/register", json=payload)
    assert register.status_code == status.HTTP_201_CREATED, register.text
    register_body = register.json()["data"]
    assert register_body["tenant"]["status"] == "trial"
    assert register_body["trial_ends_at"] is not None

    owner_token = _login(client, slug, owner_email, owner_password)
    owner_headers = _auth_headers(slug, owner_token)

    me = client.get("/api/v1/auth/me", headers=owner_headers)
    assert me.status_code == status.HTTP_200_OK
    me_data = me.json()["data"]
    assert me_data["email"] == owner_email
    assert "hospital_owner" in me_data["roles"]
    assert "*:*" in me_data["permissions"]

    profile = client.get("/api/v1/hospital/profile", headers=owner_headers)
    assert profile.status_code == status.HTTP_200_OK
    assert profile.json()["data"]["name"] == payload["name"]

    profile_update = client.patch(
        "/api/v1/hospital/profile",
        json={
            "phone": "+91-9000000001",
            "address_line1": "42 Hospital Road",
            "city": "Mumbai",
            "tax_registration_no": "GST-G2-001",
        },
        headers=owner_headers,
    )
    assert profile_update.status_code == status.HTTP_200_OK
    updated_profile = profile_update.json()["data"]
    assert updated_profile["phone"] == "+91-9000000001"
    assert updated_profile["city"] == "Mumbai"

    settings = client.get("/api/v1/hospital/settings", headers=owner_headers)
    assert settings.status_code == status.HTTP_200_OK
    settings_by_key = {s["setting_key"]: s["setting_value"] for s in settings.json()["data"]}
    assert settings_by_key["clinical"]["mrn_prefix"] == "MRN"
    assert settings_by_key["billing"]["tax_rate"] == 18.0
    assert LEGAL_ACCEPTANCE_SETTING_KEY in settings_by_key

    settings_update = client.patch(
        "/api/v1/hospital/settings",
        json={
            "settings": {
                "billing": {"tax_rate": 5.0, "tax_inclusive_pricing": True},
                "clinical": {"mrn_prefix": "G2MRN"},
                "system": {"date_format": "YYYY-MM-DD"},
            }
        },
        headers=owner_headers,
    )
    assert settings_update.status_code == status.HTTP_200_OK
    updated_settings = {s["setting_key"]: s["setting_value"] for s in settings_update.json()["data"]}
    assert updated_settings["billing"]["tax_rate"] == 5.0
    assert updated_settings["clinical"]["mrn_prefix"] == "G2MRN"
    assert updated_settings["system"]["date_format"] == "YYYY-MM-DD"

    locations = client.get("/api/v1/hospital/locations", headers=owner_headers)
    assert locations.status_code == status.HTTP_200_OK
    locs = locations.json()["data"]
    assert any(loc["code"] == "MAIN" and loc["is_primary"] for loc in locs)

    branch = client.post(
        "/api/v1/hospital/locations",
        json={"name": "G2 Branch", "code": "G2BR", "city": "Pune"},
        headers=owner_headers,
    )
    assert branch.status_code == status.HTTP_201_CREATED
    assert branch.json()["data"]["code"] == "G2BR"

    invited_email = f"g2-invited-{uuid.uuid4().hex[:8]}@example.com"
    invited_password = "InvitePass@123"
    invite = client.post(
        "/api/v1/admin/users/invite",
        json={
            "email": invited_email,
            "first_name": "G2",
            "last_name": "Receptionist",
            "role_codes": ["receptionist"],
        },
        headers=owner_headers,
    )
    assert invite.status_code == status.HTTP_201_CREATED, invite.text
    invite_body = invite.json()["data"]
    assert invite_body["status"] == "inactive"
    invite_token = invite_body["invite_token"]

    users = client.get("/api/v1/admin/users", headers=owner_headers)
    assert users.status_code == status.HTTP_200_OK
    user_emails = [u["email"] for u in users.json()["data"]]
    assert invited_email in user_emails

    accept = client.post(
        "/api/v1/auth/accept-invite",
        json={"invite_token": invite_token, "password": invited_password},
    )
    assert accept.status_code == status.HTTP_200_OK, accept.text
    accept_data = accept.json()["data"]
    assert accept_data["user"]["email"] == invited_email
    assert "receptionist" in accept_data["user"]["roles"]

    invited_token = _login(client, slug, invited_email, invited_password)
    invited_headers = _auth_headers(slug, invited_token)

    invited_me = client.get("/api/v1/auth/me", headers=invited_headers)
    assert invited_me.status_code == status.HTTP_200_OK
    invited_perms = invited_me.json()["data"]["permissions"]
    assert "admin:users" not in invited_perms
    assert "opd:read" in invited_perms or "opd:queue" in invited_perms

    denied = client.get("/api/v1/admin/users", headers=invited_headers)
    assert denied.status_code == status.HTTP_403_FORBIDDEN

    owner_still_ok = client.get("/api/v1/admin/users", headers=owner_headers)
    assert owner_still_ok.status_code == status.HTTP_200_OK


def test_g2_receptionist_cannot_update_hospital_profile(client: TestClient) -> None:
    """RBAC: clinical staff cannot mutate hospital settings."""
    payload = register_payload()
    register = client.post("/api/v1/platform/register", json=payload)
    assert register.status_code == status.HTTP_201_CREATED

    slug = payload["slug"]
    owner_headers = _auth_headers(
        slug,
        _login(client, slug, payload["email"], payload["owner_password"]),
    )

    invited_email = f"g2-rbac-{uuid.uuid4().hex[:8]}@example.com"
    invite = client.post(
        "/api/v1/admin/users/invite",
        json={
            "email": invited_email,
            "first_name": "Recv",
            "last_name": "Only",
            "role_codes": ["receptionist"],
        },
        headers=owner_headers,
    )
    assert invite.status_code == status.HTTP_201_CREATED
    invite_token = invite.json()["data"]["invite_token"]

    accept = client.post(
        "/api/v1/auth/accept-invite",
        json={"invite_token": invite_token, "password": "RecvPass@123"},
    )
    assert accept.status_code == status.HTTP_200_OK

    recv_headers = _auth_headers(
        slug,
        _login(client, slug, invited_email, "RecvPass@123"),
    )

    denied_profile = client.patch(
        "/api/v1/hospital/profile",
        json={"phone": "+91-0000000000"},
        headers=recv_headers,
    )
    assert denied_profile.status_code == status.HTTP_403_FORBIDDEN

    denied_settings = client.patch(
        "/api/v1/hospital/settings",
        json={"settings": {"billing": {"tax_rate": 99.0}}},
        headers=recv_headers,
    )
    assert denied_settings.status_code == status.HTTP_403_FORBIDDEN
