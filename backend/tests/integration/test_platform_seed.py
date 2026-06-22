"""Integration tests — MVP-015 system tenant and subscription plan seeds."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.constants import SYSTEM_TENANT_ID
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.db.subscription_plan_catalog import (
    PLAN_CODE_STARTER,
    PLAN_CODES,
    SUBSCRIPTION_PLAN_CATALOG,
)
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.domains.platform.services.plan_provisioner import PlanProvisioner

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
def test_migration_seeds_system_tenant_and_three_plans() -> None:
    """Alembic 011 must seed system tenant and starter/professional/enterprise plans."""
    _run_alembic_upgrade()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)

    with session_scope() as db:
        PlanProvisioner(db).seed_platform_catalog()
        db.commit()
        tenant = db.execute(
            text(
                """
                SELECT slug, status, email
                FROM platform.tenants
                WHERE id = :id AND deleted_at IS NULL
                """
            ),
            {"id": system_id},
        ).one()
        assert tenant.slug == "system"
        assert tenant.status == "active"
        assert tenant.email == "system@platform.com"

        rows = db.execute(
            text(
                """
                SELECT code, price_monthly::text, max_users
                FROM platform.subscription_plans
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                  AND code = ANY(:codes)
                ORDER BY code
                """
            ),
            {"tenant_id": system_id, "codes": list(PLAN_CODES)},
        ).all()
        codes = {row.code for row in rows}
        assert codes == PLAN_CODES
        assert len(rows) == 3

        starter = next(row for row in rows if row.code == PLAN_CODE_STARTER)
        catalog_starter = next(p for p in SUBSCRIPTION_PLAN_CATALOG if p.code == PLAN_CODE_STARTER)
        assert Decimal(starter.price_monthly) == catalog_starter.price_monthly
        assert starter.max_users == catalog_starter.max_users


@pytest.mark.integration
def test_plan_provisioner_seed_is_idempotent() -> None:
    """Re-running the Python provisioner must not duplicate catalog plans."""
    _run_alembic_upgrade()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)

    with session_scope() as db:
        provisioner = PlanProvisioner(db)
        provisioner.seed_platform_catalog()
        first_count = provisioner.count_active_plans(system_id)
        provisioner.seed_platform_catalog()
        second_count = provisioner.count_active_plans(system_id)
        assert first_count == 3
        assert second_count == 3


@pytest.mark.integration
def test_hospital_tenant_reads_seeded_plans_via_rls() -> None:
    """Hospital RLS context may SELECT all system-tenant subscription plans."""
    _run_alembic_upgrade()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)

    with session_scope() as db:
        PlanProvisioner(db).seed_platform_catalog()
        slug = f"seed-hosp-{uuid.uuid4().hex[:8]}"

    with session_scope() as db:
        hospital_id = TenantRepository(db).create_via_db_function(
            slug=slug,
            name="Seed Hospital",
            email=f"owner@{slug}.com",
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, hospital_id)
        rows = db.execute(
            text(
                """
                SELECT code
                FROM platform.subscription_plans
                WHERE tenant_id = :system_id
                  AND deleted_at IS NULL
                  AND code = ANY(:codes)
                ORDER BY code
                """
            ),
            {"system_id": system_id, "codes": list(PLAN_CODES)},
        ).all()
        assert [row.code for row in rows] == sorted(PLAN_CODES)


@pytest.mark.integration
def test_starter_plan_features_json_matches_catalog() -> None:
    """Seeded starter plan features JSON must match BILLING_SUBSCRIPTION.md schema."""
    _run_alembic_upgrade()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)
    catalog = next(p for p in SUBSCRIPTION_PLAN_CATALOG if p.code == PLAN_CODE_STARTER)

    with session_scope() as db:
        PlanProvisioner(db).seed_platform_catalog()
        db.commit()

        features_raw = db.execute(
            text(
                """
                SELECT features::text
                FROM platform.subscription_plans
                WHERE tenant_id = :tenant_id AND code = :code AND deleted_at IS NULL
                """
            ),
            {"tenant_id": system_id, "code": PLAN_CODE_STARTER},
        ).scalar_one()
        features = json.loads(features_raw)
        assert features == catalog.features
