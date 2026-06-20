"""Auth tables — platform.tenants, core.users, core.user_sessions.

Revision ID: 002_auth_tables
Revises: 001_database_foundation
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002_auth_tables"
down_revision: str | None = "001_database_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE platform.tenants (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL,
            name                VARCHAR(255) NOT NULL,
            slug                VARCHAR(100) NOT NULL,
            subdomain           VARCHAR(100),
            status              VARCHAR(20) NOT NULL DEFAULT 'trial'
                                CHECK (status IN ('trial', 'active', 'suspended', 'cancelled')),
            email               VARCHAR(255) NOT NULL,
            phone               VARCHAR(20),
            country             VARCHAR(100) NOT NULL DEFAULT 'IN',
            timezone            VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
            currency            VARCHAR(3) NOT NULL DEFAULT 'INR',
            metadata            JSONB,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by          UUID,
            updated_at          TIMESTAMPTZ,
            updated_by          UUID,
            deleted_at          TIMESTAMPTZ,
            deleted_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_tenants_slug ON platform.tenants (slug)")
    op.execute("CREATE UNIQUE INDEX uq_tenants_subdomain ON platform.tenants (subdomain) WHERE subdomain IS NOT NULL")
    op.execute("CREATE INDEX idx_tenants_status ON platform.tenants (status)")
    op.execute(
        """
        ALTER TABLE platform.tenants
            ADD CONSTRAINT fk_tenants_tenant_id FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
            DEFERRABLE INITIALLY DEFERRED
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_tenants_self_ref BEFORE INSERT OR UPDATE ON platform.tenants
            FOR EACH ROW EXECUTE FUNCTION platform.enforce_tenant_self_reference()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_tenants_updated_at BEFORE UPDATE ON platform.tenants
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE core.users (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id               UUID NOT NULL REFERENCES platform.tenants(id),
            email                   VARCHAR(255) NOT NULL,
            password_hash           VARCHAR(255) NOT NULL,
            first_name              VARCHAR(100) NOT NULL,
            last_name               VARCHAR(100) NOT NULL,
            phone                   VARCHAR(20),
            avatar_url              TEXT,
            status                  VARCHAR(20) NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active', 'inactive', 'locked')),
            last_login_at           TIMESTAMPTZ,
            failed_login_attempts   INTEGER NOT NULL DEFAULT 0,
            locked_until            TIMESTAMPTZ,
            email_verified_at       TIMESTAMPTZ,
            staff_id                UUID,
            location_id             UUID,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by              UUID,
            updated_at              TIMESTAMPTZ,
            updated_by              UUID,
            deleted_at              TIMESTAMPTZ,
            deleted_by              UUID,
            version                 INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_users_tenant_email ON core.users (tenant_id, email)")
    op.execute("CREATE UNIQUE INDEX uq_users_tenant_id_id ON core.users (tenant_id, id)")
    op.execute("CREATE INDEX idx_users_tenant_status ON core.users (tenant_id, status)")
    op.execute(
        """
        CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON core.users
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE core.user_sessions (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id               UUID NOT NULL REFERENCES platform.tenants(id),
            user_id                 UUID NOT NULL,
            refresh_token_hash      VARCHAR(255) NOT NULL,
            ip_address              INET,
            user_agent              TEXT,
            expires_at              TIMESTAMPTZ NOT NULL,
            revoked_at              TIMESTAMPTZ,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by              UUID,
            updated_at              TIMESTAMPTZ,
            updated_by              UUID,
            deleted_at              TIMESTAMPTZ,
            deleted_by              UUID,
            version                 INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        """
        ALTER TABLE core.user_sessions
            ADD CONSTRAINT fk_user_sessions_user FOREIGN KEY (tenant_id, user_id)
            REFERENCES core.users (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_user_sessions_token_hash ON core.user_sessions (refresh_token_hash)")
    op.execute(
        "CREATE INDEX idx_user_sessions_expires ON core.user_sessions (expires_at) WHERE revoked_at IS NULL"
    )
    op.execute(
        """
        CREATE TRIGGER trg_user_sessions_updated_at BEFORE UPDATE ON core.user_sessions
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core.user_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS core.users CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.tenants CASCADE")
