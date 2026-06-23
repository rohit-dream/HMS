"""MVP-045 — privacy/terms acceptance on tenant registration."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.domains.platform.constants import (
    CURRENT_PRIVACY_POLICY_VERSION,
    CURRENT_TERMS_VERSION,
    LEGAL_ACCEPTANCE_SETTING_KEY,
)
from app.domains.platform.repositories.setting_repository import SettingRepository
from tests.helpers.auth import register_payload

pytestmark = pytest.mark.integration


def test_get_legal_versions(client: TestClient) -> None:
    resp = client.get("/api/v1/platform/legal-versions")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()["data"]
    assert data["terms_version"] == CURRENT_TERMS_VERSION
    assert data["privacy_policy_version"] == CURRENT_PRIVACY_POLICY_VERSION
    assert "/legal/terms" in data["terms_url"]
    assert "/legal/privacy" in data["privacy_policy_url"]


def test_register_without_legal_acceptance_rejected(client: TestClient) -> None:
    payload = register_payload()
    payload["accept_terms"] = False

    resp = client.post("/api/v1/platform/register", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_records_legal_acceptance(client: TestClient) -> None:
    payload = register_payload()
    resp = client.post("/api/v1/platform/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED

    tenant_id = uuid.UUID(resp.json()["data"]["tenant"]["id"])
    slug = payload["slug"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["owner_password"]},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert login.status_code == status.HTTP_200_OK
    token = login.json()["data"]["access_token"]

    settings_resp = client.get(
        "/api/v1/hospital/settings",
        headers={TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"},
    )
    assert settings_resp.status_code == status.HTTP_200_OK
    by_key = {row["setting_key"]: row["setting_value"] for row in settings_resp.json()["data"]}
    legal = by_key[LEGAL_ACCEPTANCE_SETTING_KEY]
    assert legal["terms_version"] == CURRENT_TERMS_VERSION
    assert legal["privacy_policy_version"] == CURRENT_PRIVACY_POLICY_VERSION
    assert legal["terms_accepted"] is True
    assert legal["privacy_policy_accepted"] is True
    assert legal["accepted_by_email"] == payload["email"]
    assert legal["accepted_at"]

    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_id)
        repo = SettingRepository(db, tenant_id)
        row = repo.get_by_key(LEGAL_ACCEPTANCE_SETTING_KEY)
        assert row is not None
        assert row.setting_value["terms_version"] == CURRENT_TERMS_VERSION
