"""
MVP-020 — Gate G1 verification (Sprint 2 foundation complete).

Automated checklist for:
- Docker/CI prerequisites (file presence)
- Alembic at head with platform schema + RLS
- System tenant + subscription plan seeds
- Tenant registration API
- CF-01 isolation smoke (full suite in test_tenant_isolation.py)
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.constants import SYSTEM_TENANT_ID
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.db.rls_policies import PLATFORM_RLS_TABLES
from app.db.subscription_plan_catalog import PLAN_CODES
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.models.platform.tenant_location import TenantLocation
from app.repositories.base import TenantScopedRepository

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_ALEMBIC_HEAD = "013_email_verification_tokens"


@pytest.fixture(autouse=True)
def _reset_database_role_between_tests():
    """Prevent hms_app role leaking across pooled connections."""
    with session_scope() as db:
        db.execute(text("RESET ROLE"))
        set_rls_tenant_context(db, None)
    yield
    with session_scope() as db:
        db.execute(text("RESET ROLE"))
        set_rls_tenant_context(db, None)


PLATFORM_TABLES: tuple[str, ...] = (
    "tenants",
    "subscription_plans",
    "tenant_subscriptions",
    "tenant_locations",
    "tenant_settings",
)


def test_g1_docker_compose_files_exist() -> None:
    """G1 infra: Docker Compose definitions are present."""
    assert (REPO_ROOT / "docker-compose.yml").is_file()
    assert (REPO_ROOT / "docker-compose.test.yml").is_file()


def test_g1_ci_workflow_exists() -> None:
    """G1 infra: GitHub Actions CI pipeline is configured."""
    ci = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci.is_file()
    content = ci.read_text(encoding="utf-8")
    assert "test_tenant_isolation.py" in content


def test_g1_alembic_at_head() -> None:
    """G1 DB: all migrations through Sprint 2 are applied."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    config = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    assert head == EXPECTED_ALEMBIC_HEAD

    try:
        with engine.connect() as conn:
            current = MigrationContext.configure(conn).get_current_revision()
            assert current == EXPECTED_ALEMBIC_HEAD
    finally:
        engine.dispose()


def test_g1_platform_tables_exist() -> None:
    """G1 DB: all five platform tenant-scoped tables exist."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            for table in PLATFORM_TABLES:
                exists = conn.execute(
                    text(
                        """
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'platform' AND table_name = :table
                        """
                    ),
                    {"table": table},
                ).first()
                assert exists is not None, f"missing platform.{table}"
    finally:
        engine.dispose()


def test_g1_rls_force_enabled_on_platform_tables() -> None:
    """G1 security: FORCE ROW LEVEL SECURITY on every platform table."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            for table in PLATFORM_RLS_TABLES:
                row = conn.execute(
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
    finally:
        engine.dispose()


def test_g1_system_tenant_and_subscription_plans_seeded() -> None:
    """G1 seeds: system tenant and starter/professional/enterprise plans."""
    system_id = uuid.UUID(SYSTEM_TENANT_ID)
    with session_scope() as db:
        tenant = db.execute(
            text(
                """
                SELECT slug, status FROM platform.tenants
                WHERE id = :id AND deleted_at IS NULL
                """
            ),
            {"id": system_id},
        ).one()
        assert tenant.slug == "system"
        assert tenant.status == "active"

        plan_count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM platform.subscription_plans
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                  AND code = ANY(:codes)
                """
            ),
            {"tenant_id": system_id, "codes": list(PLAN_CODES)},
        ).scalar_one()
        assert plan_count == 3


def test_g1_platform_functions_exist() -> None:
    """G1 DB: create_tenant and lookup_tenant_for_login are deployed."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            for fn in ("create_tenant", "lookup_tenant_for_login"):
                row = conn.execute(
                    text(
                        """
                        SELECT 1 FROM pg_proc p
                        JOIN pg_namespace n ON p.pronamespace = n.oid
                        WHERE n.nspname = 'platform' AND p.proname = :fn
                        """
                    ),
                    {"fn": fn},
                ).first()
                assert row is not None, f"platform.{fn} missing"
    finally:
        engine.dispose()


def test_g1_hms_app_role_exists() -> None:
    """G1 security: hms_app role exists for non-superuser RLS tests."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'hms_app'")).first()
            assert row is not None
    finally:
        engine.dispose()


def test_g1_tenant_scoped_repository_binds_rls() -> None:
    """G1 app layer: TenantScopedRepository sets app.tenant_id on the session."""
    tenant_id = uuid.uuid4()
    with session_scope() as db:
        use_rls_enforced_role(db)
        LocationRepository(db, tenant_id)
        setting = db.execute(
            text("SELECT current_setting('app.tenant_id', true)")
        ).scalar_one()
        assert setting == str(tenant_id)


def test_g1_cf01_isolation_smoke() -> None:
    """G1 CF-01: tenant context blocks cross-tenant row visibility (smoke)."""
    slug_a = f"g1-smoke-a-{uuid.uuid4().hex[:8]}"
    tenant_b = uuid.uuid4()
    row_id = uuid.uuid4()

    with session_scope() as db:
        db.execute(text("RESET ROLE"))
        set_rls_tenant_context(db, None)
        tenant_a_id = TenantRepository(db).create_via_db_function(
            slug=slug_a,
            name="G1 Smoke A",
            email=f"{slug_a}@example.com",
        )
        set_rls_tenant_context(db, tenant_a_id)
        db.execute(
            text(
                """
                INSERT INTO platform.tenant_locations (
                    id, tenant_id, name, code, is_primary, is_active
                ) VALUES (
                    :id, :tenant_id, 'G1 Smoke', 'G1', FALSE, TRUE
                )
                """
            ),
            {"id": row_id, "tenant_id": tenant_a_id},
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_b)
        count = db.execute(
            text("SELECT COUNT(*) FROM platform.tenant_locations WHERE id = :id"),
            {"id": row_id},
        ).scalar_one()
        assert count == 0

        repo = TenantScopedRepository(db, tenant_b)
        assert repo.get_by_id(TenantLocation, row_id) is None


def test_g1_register_api_returns_201_with_tenant_id(client: TestClient) -> None:
    """G1 API: POST /platform/register provisions tenant and returns tenant id."""
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "name": f"G1 Gate Clinic {suffix}",
        "slug": f"g1-gate-{suffix}",
        "email": f"g1-{suffix}@example.com",
        "owner_first_name": "Gate",
        "owner_last_name": "Test",
        "owner_password": "SecurePass@123",
        "accept_terms": True,
        "accept_privacy_policy": True,
    }
    resp = client.post("/api/v1/platform/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()["data"]
    tenant_id = body["tenant"]["id"]
    assert uuid.UUID(tenant_id)
    assert body["tenant"]["slug"] == payload["slug"]
    assert body["tenant"]["status"] == "trial"
