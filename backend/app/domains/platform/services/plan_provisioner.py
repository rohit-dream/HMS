"""Platform catalog provisioning — system tenant subscription plans."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.constants import SYSTEM_TENANT_ID
from app.core.database import set_rls_tenant_context
from app.db.subscription_plan_catalog import (
    PLAN_CODES,
    SUBSCRIPTION_PLAN_CATALOG,
    SubscriptionPlanSeed,
)
from app.domains.identity.services.rbac_service import RbacProvisioner


class PlanProvisioner:
    """Seed subscription plan catalog under the system tenant (idempotent)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def seed_platform_catalog(self) -> uuid.UUID:
        """
        Ensure system tenant exists and all catalog plans are present.

        Safe to call multiple times (registration flow, scripts, tests).
        """
        self.db.execute(text("RESET ROLE"))
        set_rls_tenant_context(self.db, None)
        tenant_id = RbacProvisioner(self.db).ensure_system_tenant()
        for plan in SUBSCRIPTION_PLAN_CATALOG:
            self._upsert_plan(tenant_id, plan)
        self.db.flush()
        return tenant_id

    def count_active_plans(self, tenant_id: uuid.UUID | None = None) -> int:
        """Return number of active catalog plans for the system tenant."""
        system_id = tenant_id or uuid.UUID(SYSTEM_TENANT_ID)
        result = self.db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM platform.subscription_plans
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                  AND code = ANY(:codes)
                """
            ),
            {"tenant_id": system_id, "codes": list(PLAN_CODES)},
        )
        return int(result.scalar_one())

    def _upsert_plan(self, tenant_id: uuid.UUID, plan: SubscriptionPlanSeed) -> None:
        self.db.execute(
            text(
                """
                INSERT INTO platform.subscription_plans (
                    tenant_id, code, name, description,
                    price_monthly, price_annual, max_users, max_beds, max_patients,
                    features, is_active
                ) VALUES (
                    :tenant_id, :code, :name, :description,
                    :price_monthly, :price_annual, :max_users, :max_beds, :max_patients,
                    CAST(:features AS jsonb), TRUE
                )
                ON CONFLICT (tenant_id, code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price_monthly = EXCLUDED.price_monthly,
                    price_annual = EXCLUDED.price_annual,
                    max_users = EXCLUDED.max_users,
                    max_beds = EXCLUDED.max_beds,
                    max_patients = EXCLUDED.max_patients,
                    features = EXCLUDED.features,
                    is_active = EXCLUDED.is_active
                """
            ),
            {
                "tenant_id": tenant_id,
                "code": plan.code,
                "name": plan.name,
                "description": plan.description,
                "price_monthly": plan.price_monthly,
                "price_annual": plan.price_annual,
                "max_users": plan.max_users,
                "max_beds": plan.max_beds,
                "max_patients": plan.max_patients,
                "features": json.dumps(plan.features),
            },
        )
