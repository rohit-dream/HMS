"""
MVP-019 — Cross-tenant isolation regression (mandatory CI).

Verifies Tenant B cannot read or mutate Tenant A data across:
- PostgreSQL RLS (all five platform tables)
- TenantScopedRepository layer
- Hospital management API (404 on cross-tenant resource IDs)
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.constants import SYSTEM_TENANT_ID, TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import PLATFORM_RLS_TABLES
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from tests.helpers.isolation import TenantPairFixture, provision_isolated_tenant_pair
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def tenant_pair() -> TenantPairFixture:
    with session_scope() as db:
        pair = provision_isolated_tenant_pair(db)
        db.commit()
    return pair


def _assert_hidden_under_rls(
    db,
    *,
    viewer_tenant_id: uuid.UUID,
    sql: str,
    params: dict,
) -> None:
    use_rls_enforced_role(db)
    set_rls_tenant_context(db, viewer_tenant_id)
    count = db.execute(text(sql), params).scalar_one()
    assert count == 0, f"Expected 0 rows for tenant {viewer_tenant_id}, got {count}"


def _assert_visible_under_rls(
    db,
    *,
    viewer_tenant_id: uuid.UUID,
    sql: str,
    params: dict,
) -> None:
    use_rls_enforced_role(db)
    set_rls_tenant_context(db, viewer_tenant_id)
    count = db.execute(text(sql), params).scalar_one()
    assert count == 1, f"Expected 1 row for tenant {viewer_tenant_id}, got {count}"


class TestPlatformRlsIsolation:
    """Direct SQL under hms_app — all platform tenant-scoped tables."""

    def test_tenant_b_cannot_see_tenant_a_location(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            _assert_hidden_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_b.tenant_id,
                sql="SELECT COUNT(*) FROM platform.tenant_locations WHERE id = :id",
                params={"id": tenant_pair.tenant_a.location_id},
            )
            _assert_visible_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_a.tenant_id,
                sql="SELECT COUNT(*) FROM platform.tenant_locations WHERE id = :id",
                params={"id": tenant_pair.tenant_a.location_id},
            )

    def test_tenant_b_cannot_see_tenant_a_settings(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            _assert_hidden_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_b.tenant_id,
                sql=(
                    "SELECT COUNT(*) FROM platform.tenant_settings "
                    "WHERE id = :id"
                ),
                params={"id": tenant_pair.tenant_a.setting_id},
            )

    def test_tenant_b_cannot_see_tenant_a_subscription(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            _assert_hidden_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_b.tenant_id,
                sql=(
                    "SELECT COUNT(*) FROM platform.tenant_subscriptions "
                    "WHERE id = :id"
                ),
                params={"id": tenant_pair.tenant_a.subscription_id},
            )

    def test_tenant_b_cannot_see_tenant_a_tenant_row(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            _assert_hidden_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_b.tenant_id,
                sql="SELECT COUNT(*) FROM platform.tenants WHERE id = :id",
                params={"id": tenant_pair.tenant_a.tenant_id},
            )
            _assert_visible_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_a.tenant_id,
                sql="SELECT COUNT(*) FROM platform.tenants WHERE id = :id",
                params={"id": tenant_pair.tenant_a.tenant_id},
            )

    def test_tenant_b_can_read_system_subscription_plans(self, tenant_pair: TenantPairFixture) -> None:
        """System-tenant catalog plans remain readable (intentional RLS exception)."""
        system_id = uuid.UUID(SYSTEM_TENANT_ID)
        with session_scope() as db:
            use_rls_enforced_role(db)
            set_rls_tenant_context(db, tenant_pair.tenant_b.tenant_id)
            count = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM platform.subscription_plans
                    WHERE tenant_id = :system_id AND code = 'starter' AND deleted_at IS NULL
                    """
                ),
                {"system_id": system_id},
            ).scalar_one()
            assert count == 1

    def test_hospital_scoped_plan_not_visible_to_other_tenant(
        self, tenant_pair: TenantPairFixture
    ) -> None:
        """Custom plans under a hospital tenant_id are not shared."""
        custom_plan_id = uuid.uuid4()
        with session_scope() as db:
            db.execute(text("RESET ROLE"))
            set_rls_tenant_context(db, None)
            db.execute(
                text(
                    """
                    INSERT INTO platform.subscription_plans (
                        id, tenant_id, code, name, price_monthly, max_users, features, is_active
                    ) VALUES (
                        :id, :tenant_id, :code, 'Private', 1.00, 1, '{}', TRUE
                    )
                    """
                ),
                {
                    "id": custom_plan_id,
                    "tenant_id": tenant_pair.tenant_a.tenant_id,
                    "code": f"private-{tenant_pair.tenant_a.tenant_id.hex[:8]}",
                },
            )
            db.commit()

            _assert_hidden_under_rls(
                db,
                viewer_tenant_id=tenant_pair.tenant_b.tenant_id,
                sql="SELECT COUNT(*) FROM platform.subscription_plans WHERE id = :id",
                params={"id": custom_plan_id},
            )

    @pytest.mark.parametrize("table", PLATFORM_RLS_TABLES)
    def test_all_platform_tables_have_force_rls(self, table: str) -> None:
        with session_scope() as db:
            row = db.execute(
                text(
                    """
                    SELECT c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'platform' AND c.relname = :table
                    """
                ),
                {"table": table},
            ).one()
            assert row[0] is True, f"{table}: RLS not enabled"
            assert row[1] is True, f"{table}: FORCE RLS not enabled"

    def test_missing_tenant_context_returns_no_rows(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            set_rls_tenant_context(db, None)
            count = db.execute(
                text("SELECT COUNT(*) FROM platform.tenant_locations WHERE id = :id"),
                {"id": tenant_pair.tenant_a.location_id},
            ).scalar_one()
            assert count == 0


class TestRepositoryIsolation:
    """TenantScopedRepository must not return cross-tenant rows."""

    def test_location_repository_get_by_id_isolated(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = LocationRepository(db, tenant_pair.tenant_b.tenant_id)
            assert repo_b.get_by_id(tenant_pair.tenant_a.location_id) is None

            repo_a = LocationRepository(db, tenant_pair.tenant_a.tenant_id)
            location = repo_a.get_by_id(tenant_pair.tenant_a.location_id)
            assert location is not None
            assert location.tenant_id == tenant_pair.tenant_a.tenant_id

    def test_setting_repository_get_by_key_isolated(self, tenant_pair: TenantPairFixture) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = SettingRepository(db, tenant_pair.tenant_b.tenant_id)
            assert repo_b.get_by_key("isolation_marker_tenant_a") is None

            repo_a = SettingRepository(db, tenant_pair.tenant_a.tenant_id)
            setting = repo_a.get_by_key("isolation_marker_tenant_a")
            assert setting is not None
            assert setting.tenant_id == tenant_pair.tenant_a.tenant_id

    def test_location_repository_list_excludes_other_tenant(
        self, tenant_pair: TenantPairFixture
    ) -> None:
        with session_scope() as db:
            use_rls_enforced_role(db)
            repo_b = LocationRepository(db, tenant_pair.tenant_b.tenant_id)
            ids = {loc.id for loc in repo_b.list_active()}
            assert tenant_pair.tenant_a.location_id not in ids


class TestApiIsolation:
    """Authenticated API must scope all reads/writes to JWT tenant."""

    @staticmethod
    def _auth_headers(client: TestClient, slug: str, email: str) -> dict[str, str]:
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass@123"},
            headers={TENANT_SLUG_HEADER: slug},
        )
        assert resp.status_code == status.HTTP_200_OK
        token = resp.json()["data"]["access_token"]
        return {TENANT_SLUG_HEADER: slug, "Authorization": f"Bearer {token}"}

    @pytest.fixture
    def api_tenant_pair(self, client: TestClient) -> dict:
        suffix_a = uuid.uuid4().hex[:8]
        suffix_b = uuid.uuid4().hex[:8]
        slug_a = f"api-iso-a-{suffix_a}"
        slug_b = f"api-iso-b-{suffix_b}"
        email_a = f"admin-a-{suffix_a}@example.com"
        email_b = f"admin-b-{suffix_b}@example.com"

        with session_scope() as db:
            data_a = provision_tenant_with_role(
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

            loc_a = LocationRepository(db, data_a["tenant_id"]).create(
                name="Tenant A Secret Branch",
                code="SECRET-A",
                is_primary=False,
                is_active=True,
            )
            db.commit()
            location_a_id = loc_a.id

        return {
            "slug_a": slug_a,
            "slug_b": slug_b,
            "email_a": email_a,
            "email_b": email_b,
            "tenant_a_id": data_a["tenant_id"],
            "tenant_b_id": data_b["tenant_id"],
            "location_a_id": location_a_id,
        }

    def test_api_cannot_patch_other_tenant_location(
        self, client: TestClient, api_tenant_pair: dict
    ) -> None:
        headers_b = self._auth_headers(
            client, api_tenant_pair["slug_b"], api_tenant_pair["email_b"]
        )
        resp = client.patch(
            f"/api/v1/hospital/locations/{api_tenant_pair['location_a_id']}",
            json={"name": "Hijacked"},
            headers=headers_b,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_api_location_list_excludes_other_tenant_branches(
        self, client: TestClient, api_tenant_pair: dict
    ) -> None:
        headers_b = self._auth_headers(
            client, api_tenant_pair["slug_b"], api_tenant_pair["email_b"]
        )
        resp = client.get("/api/v1/hospital/locations", headers=headers_b)
        assert resp.status_code == status.HTTP_200_OK
        codes = {item["code"] for item in resp.json()["data"]}
        assert "SECRET-A" not in codes

    def test_api_profile_scoped_to_jwt_tenant(
        self, client: TestClient, api_tenant_pair: dict
    ) -> None:
        headers_a = self._auth_headers(
            client, api_tenant_pair["slug_a"], api_tenant_pair["email_a"]
        )
        headers_b = self._auth_headers(
            client, api_tenant_pair["slug_b"], api_tenant_pair["email_b"]
        )

        profile_a = client.get("/api/v1/hospital/profile", headers=headers_a).json()["data"]
        profile_b = client.get("/api/v1/hospital/profile", headers=headers_b).json()["data"]

        assert profile_a["id"] == str(api_tenant_pair["tenant_a_id"])
        assert profile_b["id"] == str(api_tenant_pair["tenant_b_id"])
        assert profile_a["slug"] == api_tenant_pair["slug_a"]
        assert profile_b["slug"] == api_tenant_pair["slug_b"]

    def test_api_settings_do_not_leak_across_tenants(
        self, client: TestClient, api_tenant_pair: dict
    ) -> None:
        headers_a = self._auth_headers(
            client, api_tenant_pair["slug_a"], api_tenant_pair["email_a"]
        )
        headers_b = self._auth_headers(
            client, api_tenant_pair["slug_b"], api_tenant_pair["email_b"]
        )

        put_resp = client.put(
            "/api/v1/hospital/settings/isolation_api_secret",
            json={"setting_value": {"secret": "tenant-a-only"}, "description": "API isolation"},
            headers=headers_a,
        )
        assert put_resp.status_code == status.HTTP_200_OK

        list_b = client.get("/api/v1/hospital/settings", headers=headers_b)
        assert list_b.status_code == status.HTTP_200_OK
        keys_b = {item["setting_key"] for item in list_b.json()["data"]}
        assert "isolation_api_secret" not in keys_b

        list_a = client.get("/api/v1/hospital/settings", headers=headers_a)
        keys_a = {item["setting_key"] for item in list_a.json()["data"]}
        assert "isolation_api_secret" in keys_a
