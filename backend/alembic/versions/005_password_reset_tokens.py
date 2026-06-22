"""Password reset tokens — core.password_reset_tokens.

Revision ID: 005_password_reset_tokens
Revises: 004_platform_hospital
"""

from collections.abc import Sequence

from alembic import op

revision: str = "005_password_reset_tokens"
down_revision: str | None = "004_platform_hospital"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE core.password_reset_tokens (
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
        "CREATE UNIQUE INDEX uq_password_reset_tokens_tenant_id_id ON core.password_reset_tokens (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.password_reset_tokens
            ADD CONSTRAINT fk_password_reset_tokens_user FOREIGN KEY (tenant_id, user_id)
            REFERENCES core.users (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_password_reset_tokens_hash ON core.password_reset_tokens (token_hash)"
    )
    op.execute(
        """
        CREATE TRIGGER trg_password_reset_tokens_updated_at BEFORE UPDATE ON core.password_reset_tokens
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core.password_reset_tokens CASCADE")
