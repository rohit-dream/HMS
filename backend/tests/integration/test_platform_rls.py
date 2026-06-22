"""Integration tests — MVP-012 platform RLS policies."""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.constants import SYSTEM_TENANT_ID
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.db.rls_policies import PLATFORM_RLS_TABLES

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.integration
def test_platform_tables_have_rls_enabled() -> None:
    """All five platform tables must have RLS + FORCE RLS after migration 007."""
    _run_alembic_upgrade()
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

                policy_count = conn.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM pg_policies
                        WHERE schemaname = 'platform' AND tablename = :table
                        """
                    ),
                    {"table": table},
                ).scalar_one()
                assert policy_count == 4, f"{table}: expected 4 policies, got {policy_count}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_rls_hides_tenant_locations_from_other_tenant() -> None:
    """Tenant B context must not see Tenant A locations via direct SQL."""
    _run_alembic_upgrade()
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    location_id = uuid.uuid4()
    slug_a = f"rls-a-{tenant_a.hex[:8]}"
    slug_b = f"rls-b-{tenant_b.hex[:8]}"

    with session_scope() as db:
        use_rls_enforced_role(db)
        for tenant_id, slug in ((tenant_a, slug_a), (tenant_b, slug_b)):
            set_rls_tenant_context(db, tenant_id)
            db.execute(
                text(
                    """
                    INSERT INTO platform.tenants (
                        id, tenant_id, name, slug, subdomain, status, email
                    ) VALUES (
                        :id, :tenant_id, :name, :slug, :slug, 'active', :email
                    )
                    """
                ),
                {
                    "id": tenant_id,
                    "tenant_id": tenant_id,
                    "name": f"Hospital {slug}",
                    "slug": slug,
                    "email": f"{slug}@example.com",
                },
            )

        set_rls_tenant_context(db, tenant_a)
        db.execute(
            text(
                """
                INSERT INTO platform.tenant_locations (
                    id, tenant_id, name, code, is_primary, is_active
                ) VALUES (
                    :id, :tenant_id, 'Branch A', 'A1', TRUE, TRUE
                )
                """
            ),
            {"id": location_id, "tenant_id": tenant_a},
        )

        set_rls_tenant_context(db, tenant_b)
        count = db.execute(
            text("SELECT COUNT(*) FROM platform.tenant_locations WHERE id = :id"),
            {"id": location_id},
        ).scalar_one()
        assert count == 0

        set_rls_tenant_context(db, tenant_a)
        visible = db.execute(
            text("SELECT COUNT(*) FROM platform.tenant_locations WHERE id = :id"),
            {"id": location_id},
        ).scalar_one()
        assert visible == 1


@pytest.mark.integration
def test_rls_missing_context_returns_no_tenant_rows() -> None:
    """Without app.tenant_id, tenant-scoped SELECT returns zero rows (fail-safe)."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            conn.execute(text("SET ROLE hms_app"))
            conn.execute(text("RESET app.tenant_id"))
            count = conn.execute(text("SELECT COUNT(*) FROM platform.tenant_locations")).scalar_one()
            assert count == 0
            conn.execute(text("RESET ROLE"))
    finally:
        engine.dispose()


@pytest.mark.integration
def test_subscription_plans_system_tenant_readable_by_hospital() -> None:
    """Hospital tenants may SELECT plans seeded under the system tenant."""
    _run_alembic_upgrade()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)
    hospital_id = uuid.uuid4()

    with session_scope() as db:
        use_rls_enforced_role(db)

        plan_row = db.execute(
            text(
                """
                SELECT id, code
                FROM platform.subscription_plans
                WHERE tenant_id = :tenant_id AND code = 'starter' AND deleted_at IS NULL
                """
            ),
            {"tenant_id": system_id},
        ).one()
        plan_id = plan_row.id
        plan_code = plan_row.code

        hospital_slug = f"apollo-{hospital_id.hex[:8]}"
        set_rls_tenant_context(db, hospital_id)
        db.execute(
            text(
                """
                INSERT INTO platform.tenants (
                    id, tenant_id, name, slug, subdomain, status, email
                ) VALUES (
                    :id, :tenant_id, 'Apollo', :slug, :slug, 'active', :email
                )
                """
            ),
            {
                "id": hospital_id,
                "tenant_id": hospital_id,
                "slug": hospital_slug,
                "email": f"a@{hospital_slug}.com",
            },
        )

        set_rls_tenant_context(db, hospital_id)
        row = db.execute(
            text("SELECT code FROM platform.subscription_plans WHERE id = :id"),
            {"id": plan_id},
        ).first()
        assert row is not None
        assert row[0] == plan_code


@pytest.mark.integration
def test_create_tenant_function_works_with_rls() -> None:
    """SECURITY DEFINER create_tenant must insert tenant rows when RLS is active."""
    _run_alembic_upgrade()
    slug = f"rls-clinic-{uuid.uuid4().hex[:8]}"

    with session_scope() as db:
        new_id = db.execute(
            text(
                """
                SELECT platform.create_tenant(
                    :name, :slug, :email, :slug
                )
                """
            ),
            {
                "name": "RLS Clinic",
                "slug": slug,
                "email": f"owner@{slug}.com",
            },
        ).scalar_one()
        tenant_uuid = uuid.UUID(str(new_id))

        set_rls_tenant_context(db, tenant_uuid)
        row = db.execute(
            text("SELECT slug FROM platform.tenants WHERE id = :id"),
            {"id": tenant_uuid},
        ).first()
        assert row is not None
        assert row[0] == slug


@pytest.mark.integration
def test_lookup_tenant_for_login_bypasses_rls() -> None:
    """Pre-auth tenant resolution uses SECURITY DEFINER lookup."""
    _run_alembic_upgrade()
    slug = f"login-test-{uuid.uuid4().hex[:8]}"

    with session_scope() as db:
        db.execute(text("RESET app.tenant_id"))
        db.execute(
            text(
                """
                SELECT platform.create_tenant(
                    'Login Test', :slug, :email, :slug
                )
                """
            ),
            {"slug": slug, "email": f"login@{slug}.com"},
        )

        db.execute(text("RESET app.tenant_id"))
        row = db.execute(
            text("SELECT slug, status FROM platform.lookup_tenant_for_login(:slug)"),
            {"slug": slug},
        ).first()
        assert row is not None
        assert row[0] == slug
