"""Reusable SQL fragments for tenant RLS policies in Alembic migrations."""

from __future__ import annotations

SYSTEM_TENANT_ID = "00000000-0000-0000-0000-000000000001"

PLATFORM_RLS_TABLES: tuple[str, ...] = (
    "tenants",
    "subscription_plans",
    "tenant_subscriptions",
    "tenant_locations",
    "tenant_settings",
)

TENANT_ISOLATION_USING = (
    "tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid"
)

SUBSCRIPTION_PLANS_SELECT_USING = (
    f"tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid "
    f"OR tenant_id = '{SYSTEM_TENANT_ID}'::uuid"
)


def enable_rls_statements(schema: str, table: str) -> list[str]:
    """ENABLE + FORCE ROW LEVEL SECURITY."""
    qualified = f"{schema}.{table}"
    return [
        f"ALTER TABLE {qualified} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {qualified} FORCE ROW LEVEL SECURITY",
    ]


def tenant_isolation_policy_statements(
    schema: str,
    table: str,
    *,
    select_using: str | None = None,
) -> list[str]:
    """Standard four-policy tenant isolation pack."""
    qualified = f"{schema}.{table}"
    using = select_using or TENANT_ISOLATION_USING
    return [
        f"CREATE POLICY tenant_isolation_select ON {qualified} "
        f"FOR SELECT USING ({using})",
        f"CREATE POLICY tenant_isolation_insert ON {qualified} "
        f"FOR INSERT WITH CHECK ({TENANT_ISOLATION_USING})",
        f"CREATE POLICY tenant_isolation_update ON {qualified} "
        f"FOR UPDATE USING ({TENANT_ISOLATION_USING}) "
        f"WITH CHECK ({TENANT_ISOLATION_USING})",
        f"CREATE POLICY tenant_isolation_delete ON {qualified} "
        f"FOR DELETE USING ({TENANT_ISOLATION_USING})",
    ]


def disable_rls_statements(schema: str, table: str) -> list[str]:
    """Drop policies and disable RLS (downgrade)."""
    qualified = f"{schema}.{table}"
    return [
        f"DROP POLICY IF EXISTS tenant_isolation_select ON {qualified}",
        f"DROP POLICY IF EXISTS tenant_isolation_insert ON {qualified}",
        f"DROP POLICY IF EXISTS tenant_isolation_update ON {qualified}",
        f"DROP POLICY IF EXISTS tenant_isolation_delete ON {qualified}",
        f"ALTER TABLE {qualified} DISABLE ROW LEVEL SECURITY",
    ]
