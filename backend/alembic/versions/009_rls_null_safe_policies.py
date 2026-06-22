"""Fix RLS policies — NULLIF on app.tenant_id avoids invalid ''::uuid cast.

Revision ID: 009_rls_null_safe_policies
Revises: 008_hms_app_role
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    PLATFORM_RLS_TABLES,
    SUBSCRIPTION_PLANS_SELECT_USING,
    disable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "009_rls_null_safe_policies"
down_revision: str | None = "008_hms_app_role"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in PLATFORM_RLS_TABLES:
        for statement in disable_rls_statements("platform", table):
            if "DISABLE ROW LEVEL SECURITY" not in statement:
                op.execute(statement)

        select_using = (
            SUBSCRIPTION_PLANS_SELECT_USING if table == "subscription_plans" else None
        )
        for statement in tenant_isolation_policy_statements(
            "platform",
            table,
            select_using=select_using,
        ):
            op.execute(statement)


def downgrade() -> None:
    old_using = "tenant_id = current_setting('app.tenant_id', true)::uuid"
    old_plans_select = (
        "tenant_id = current_setting('app.tenant_id', true)::uuid "
        "OR tenant_id = '00000000-0000-0000-0000-000000000001'::uuid"
    )

    for table in PLATFORM_RLS_TABLES:
        for statement in disable_rls_statements("platform", table):
            if "DISABLE ROW LEVEL SECURITY" not in statement:
                op.execute(statement)

        select_using = old_plans_select if table == "subscription_plans" else old_using
        for statement in tenant_isolation_policy_statements(
            "platform",
            table,
            select_using=select_using,
        ):
            op.execute(statement)
