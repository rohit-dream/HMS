"""Helpers for cross-tenant isolation integration tests (MVP-019)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.constants import SYSTEM_TENANT_ID
from app.core.database import set_rls_tenant_context
from app.db.subscription_plan_catalog import PLAN_CODE_STARTER
from app.domains.platform.constants import DEFAULT_TENANT_SETTINGS
from app.domains.platform.repositories.location_repository import LocationRepository
from app.domains.platform.repositories.setting_repository import SettingRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.domains.platform.services.plan_provisioner import PlanProvisioner


@dataclass(frozen=True)
class IsolatedTenantFixture:
    tenant_id: uuid.UUID
    slug: str
    location_id: uuid.UUID
    setting_id: uuid.UUID
    subscription_id: uuid.UUID


@dataclass(frozen=True)
class TenantPairFixture:
    tenant_a: IsolatedTenantFixture
    tenant_b: IsolatedTenantFixture
    plan_id: uuid.UUID


def provision_isolated_tenant_pair(db: Session) -> TenantPairFixture:
    """
    Create two tenants with distinct platform rows for isolation regression.

    Runs as the database superuser (before SET ROLE hms_app).
    """
    db.execute(text("RESET ROLE"))
    set_rls_tenant_context(db, None)

    PlanProvisioner(db).seed_platform_catalog()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)
    plan_id = db.execute(
        text(
            """
            SELECT id FROM platform.subscription_plans
            WHERE tenant_id = :tenant_id AND code = :code AND deleted_at IS NULL
            """
        ),
        {"tenant_id": system_id, "code": PLAN_CODE_STARTER},
    ).scalar_one()

    tenant_repo = TenantRepository(db)
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    slug_a = f"iso-a-{suffix_a}"
    slug_b = f"iso-b-{suffix_b}"

    tenant_a_id = tenant_repo.create_via_db_function(
        name=f"Isolation Hospital A {suffix_a}",
        slug=slug_a,
        email=f"owner-a-{suffix_a}@example.com",
    )
    tenant_b_id = tenant_repo.create_via_db_function(
        name=f"Isolation Hospital B {suffix_b}",
        slug=slug_b,
        email=f"owner-b-{suffix_b}@example.com",
    )

    tenants: list[IsolatedTenantFixture] = []
    for tenant_id, slug, marker in (
        (tenant_a_id, slug_a, "tenant_a"),
        (tenant_b_id, slug_b, "tenant_b"),
    ):
        location_id = uuid.uuid4()
        setting_id = uuid.uuid4()
        subscription_id = uuid.uuid4()
        period_end = datetime.now(UTC) + timedelta(days=14)

        db.execute(
            text(
                """
                INSERT INTO platform.tenant_locations (
                    id, tenant_id, name, code, is_primary, is_active
                ) VALUES (
                    :id, :tenant_id, :name, :code, FALSE, TRUE
                )
                """
            ),
            {
                "id": location_id,
                "tenant_id": tenant_id,
                "name": f"{marker} branch",
                "code": f"ISO-{marker[-1].upper()}",
            },
        )

        db.execute(
            text(
                """
                INSERT INTO platform.tenant_settings (
                    id, tenant_id, setting_key, setting_value, description
                ) VALUES (
                    :id, :tenant_id, :setting_key, CAST(:setting_value AS jsonb), :description
                )
                """
            ),
            {
                "id": setting_id,
                "tenant_id": tenant_id,
                "setting_key": f"isolation_marker_{marker}",
                "setting_value": f'{{"marker": "{marker}"}}',
                "description": f"Isolation test marker for {marker}",
            },
        )

        db.execute(
            text(
                """
                INSERT INTO platform.tenant_subscriptions (
                    id, tenant_id, plan_id, status, billing_cycle,
                    current_period_start, current_period_end
                ) VALUES (
                    :id, :tenant_id, :plan_id, 'trial', 'monthly',
                    NOW(), :period_end
                )
                """
            ),
            {
                "id": subscription_id,
                "tenant_id": tenant_id,
                "plan_id": plan_id,
                "period_end": period_end,
            },
        )

        setting_repo = SettingRepository(db, tenant_id)
        setting_repo.seed_defaults(DEFAULT_TENANT_SETTINGS)

        tenants.append(
            IsolatedTenantFixture(
                tenant_id=tenant_id,
                slug=slug,
                location_id=location_id,
                setting_id=setting_id,
                subscription_id=subscription_id,
            )
        )

    db.flush()
    return TenantPairFixture(tenant_a=tenants[0], tenant_b=tenants[1], plan_id=plan_id)
