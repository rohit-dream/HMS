"""core.email_verification_tokens — email verification workflow (MVP-022).

Revision ID: 013_email_verification_tokens
Revises: 012_core_auth_rls
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "013_email_verification_tokens"
down_revision: str | None = "012_core_auth_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "email_verification_tokens"


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE core.email_verification_tokens (
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
        "COMMENT ON TABLE core.email_verification_tokens IS "
        "'One-time email verification tokens (hashed at rest, 24h expiry).'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_email_verification_tokens_tenant_id_id "
        "ON core.email_verification_tokens (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.email_verification_tokens
            ADD CONSTRAINT fk_email_verification_tokens_user
            FOREIGN KEY (tenant_id, user_id)
            REFERENCES core.users (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_email_verification_tokens_hash "
        "ON core.email_verification_tokens (token_hash)"
    )
    op.execute(
        """
        CREATE INDEX idx_email_verification_tokens_user_active
        ON core.email_verification_tokens (tenant_id, user_id)
        WHERE used_at IS NULL AND deleted_at IS NULL
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER trg_{_TABLE}_updated_at BEFORE UPDATE ON core.{_TABLE}
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    for stmt in enable_rls_statements("core", _TABLE):
        op.execute(stmt)
    for stmt in tenant_isolation_policy_statements("core", _TABLE):
        op.execute(stmt)

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO hms_app"
    )


def downgrade() -> None:
    for stmt in disable_rls_statements("core", _TABLE):
        op.execute(stmt)
    op.execute(f"DROP TABLE IF EXISTS core.{_TABLE} CASCADE")
