"""FORCE ROW LEVEL SECURITY on core auth tables — MVP-021.

Applies tenant isolation policies to:
- core.users
- core.user_sessions
- core.password_reset_tokens

Revision ID: 012_core_auth_rls
Revises: 011_system_tenant_plans_seed
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    CORE_AUTH_RLS_TABLES,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "012_core_auth_rls"
down_revision: str | None = "011_system_tenant_plans_seed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in CORE_AUTH_RLS_TABLES:
        for stmt in enable_rls_statements("core", table):
            op.execute(stmt)
        for stmt in tenant_isolation_policy_statements("core", table):
            op.execute(stmt)

    # Tables created after 008_hms_app_role must be granted explicitly.
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO hms_app"
    )


def downgrade() -> None:
    for table in reversed(CORE_AUTH_RLS_TABLES):
        for stmt in disable_rls_statements("core", table):
            op.execute(stmt)
