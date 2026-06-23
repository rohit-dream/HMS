"""MVP-036 — core.user_invite_tokens + FORCE RLS on RBAC tables.

Sprint 4 logical migration: 004_rbac_invite_tables

Revision ID: 015_rbac_invite_rls
Revises: 014_audit_audit_logs
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    CORE_RBAC_RLS_TABLES,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "015_rbac_invite_rls"
down_revision: str | None = "014_audit_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INVITE_TABLE = "user_invite_tokens"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE core.{_INVITE_TABLE} (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            user_id         UUID NOT NULL,
            token_hash      VARCHAR(255) NOT NULL,
            expires_at      TIMESTAMPTZ NOT NULL,
            used_at         TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        f"COMMENT ON TABLE core.{_INVITE_TABLE} IS "
        "'One-time user invite tokens (hashed at rest, 72h expiry).'"
    )
    op.execute(
        f"CREATE UNIQUE INDEX uq_{_INVITE_TABLE}_tenant_id_id "
        f"ON core.{_INVITE_TABLE} (tenant_id, id)"
    )
    op.execute(
        f"""
        ALTER TABLE core.{_INVITE_TABLE}
            ADD CONSTRAINT fk_{_INVITE_TABLE}_user
            FOREIGN KEY (tenant_id, user_id)
            REFERENCES core.users (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        f"CREATE INDEX idx_{_INVITE_TABLE}_hash ON core.{_INVITE_TABLE} (token_hash)"
    )
    op.execute(
        f"""
        CREATE INDEX idx_{_INVITE_TABLE}_user_active
        ON core.{_INVITE_TABLE} (tenant_id, user_id)
        WHERE used_at IS NULL AND deleted_at IS NULL
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER trg_{_INVITE_TABLE}_updated_at BEFORE UPDATE ON core.{_INVITE_TABLE}
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    for stmt in enable_rls_statements("core", _INVITE_TABLE):
        op.execute(stmt)
    for stmt in tenant_isolation_policy_statements("core", _INVITE_TABLE):
        op.execute(stmt)

    for table in CORE_RBAC_RLS_TABLES:
        for stmt in enable_rls_statements("core", table):
            op.execute(stmt)
        for stmt in tenant_isolation_policy_statements("core", table):
            op.execute(stmt)

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO hms_app"
    )


def downgrade() -> None:
    for table in reversed(CORE_RBAC_RLS_TABLES):
        for stmt in disable_rls_statements("core", table):
            op.execute(stmt)

    for stmt in disable_rls_statements("core", _INVITE_TABLE):
        op.execute(stmt)
    op.execute(f"DROP TABLE IF EXISTS core.{_INVITE_TABLE} CASCADE")
