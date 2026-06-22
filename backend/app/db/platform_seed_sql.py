"""Idempotent SQL seeds for system tenant and subscription plan catalog."""

from __future__ import annotations

import json

from app.db.subscription_plan_catalog import SUBSCRIPTION_PLAN_CATALOG, SYSTEM_TENANT_SEED


def system_tenant_seed_sql() -> str:
    """Insert the platform system tenant if missing."""
    return f"""
    INSERT INTO platform.tenants (
        id, tenant_id, name, slug, subdomain, status, email,
        country, timezone, currency
    ) VALUES (
        '{SYSTEM_TENANT_SEED["id"]}'::uuid,
        '{SYSTEM_TENANT_SEED["id"]}'::uuid,
        '{SYSTEM_TENANT_SEED["name"]}',
        '{SYSTEM_TENANT_SEED["slug"]}',
        '{SYSTEM_TENANT_SEED["subdomain"]}',
        '{SYSTEM_TENANT_SEED["status"]}',
        '{SYSTEM_TENANT_SEED["email"]}',
        '{SYSTEM_TENANT_SEED["country"]}',
        '{SYSTEM_TENANT_SEED["timezone"]}',
        '{SYSTEM_TENANT_SEED["currency"]}'
    )
    ON CONFLICT (id) DO NOTHING
    """


def subscription_plans_seed_sql() -> str:
    """Insert starter, professional, and enterprise plans under the system tenant."""
    value_rows: list[str] = []
    system_id = SYSTEM_TENANT_SEED["id"]

    for plan in SUBSCRIPTION_PLAN_CATALOG:
        features_json = json.dumps(plan.features).replace("'", "''")
        price_annual = "NULL" if plan.price_annual is None else str(plan.price_annual)
        max_beds = "NULL" if plan.max_beds is None else str(plan.max_beds)
        max_patients = "NULL" if plan.max_patients is None else str(plan.max_patients)
        description = plan.description.replace("'", "''")

        value_rows.append(
            f"""(
                gen_random_uuid(),
                '{system_id}'::uuid,
                '{plan.code}',
                '{plan.name}',
                '{description}',
                {plan.price_monthly},
                {price_annual},
                {plan.max_users},
                {max_beds},
                {max_patients},
                '{features_json}'::jsonb,
                TRUE
            )"""
        )

    values_sql = ",\n        ".join(value_rows)
    return f"""
    INSERT INTO platform.subscription_plans (
        id, tenant_id, code, name, description,
        price_monthly, price_annual, max_users, max_beds, max_patients,
        features, is_active
    ) VALUES
        {values_sql}
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


def subscription_plans_seed_downgrade_sql() -> str:
    """Remove seeded catalog plans (system tenant row retained for RBAC)."""
    codes = ", ".join(f"'{plan.code}'" for plan in SUBSCRIPTION_PLAN_CATALOG)
    system_id = SYSTEM_TENANT_SEED["id"]
    return f"""
    DELETE FROM platform.subscription_plans
    WHERE tenant_id = '{system_id}'::uuid
      AND code IN ({codes})
    """
