"""Platform hospital tables — tenant profile columns, locations, settings.

Revision ID: 004_platform_hospital
Revises: 003_rbac_tables
"""

from collections.abc import Sequence

from alembic import op

revision: str = "004_platform_hospital"
down_revision: str | None = "003_rbac_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE platform.tenants
            ADD COLUMN IF NOT EXISTS logo_url TEXT,
            ADD COLUMN IF NOT EXISTS address_line1 VARCHAR(255),
            ADD COLUMN IF NOT EXISTS address_line2 VARCHAR(255),
            ADD COLUMN IF NOT EXISTS city VARCHAR(100),
            ADD COLUMN IF NOT EXISTS state VARCHAR(100),
            ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
            ADD COLUMN IF NOT EXISTS tax_registration_no VARCHAR(50)
        """
    )

    op.execute(
        """
        CREATE TABLE platform.tenant_locations (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            name            VARCHAR(255) NOT NULL,
            code            VARCHAR(20) NOT NULL,
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            address_line1   VARCHAR(255),
            city            VARCHAR(100),
            state           VARCHAR(100),
            phone           VARCHAR(20),
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
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
        "CREATE UNIQUE INDEX uq_tenant_locations_tenant_id_id ON platform.tenant_locations (tenant_id, id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_tenant_locations_tenant_code ON platform.tenant_locations (tenant_id, code)"
    )
    op.execute("CREATE INDEX idx_tenant_locations_tenant_id ON platform.tenant_locations (tenant_id)")
    op.execute(
        """
        CREATE TRIGGER trg_tenant_locations_updated_at BEFORE UPDATE ON platform.tenant_locations
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE platform.tenant_settings (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            setting_key     VARCHAR(100) NOT NULL,
            setting_value   JSONB NOT NULL DEFAULT '{}',
            description     TEXT,
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
        "CREATE UNIQUE INDEX uq_tenant_settings_tenant_id_id ON platform.tenant_settings (tenant_id, id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_tenant_settings_tenant_key ON platform.tenant_settings (tenant_id, setting_key)"
    )
    op.execute("CREATE INDEX idx_tenant_settings_tenant_id ON platform.tenant_settings (tenant_id)")
    op.execute(
        """
        CREATE TRIGGER trg_tenant_settings_updated_at BEFORE UPDATE ON platform.tenant_settings
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION platform.create_tenant(
            p_name      VARCHAR,
            p_slug      VARCHAR,
            p_email     VARCHAR,
            p_subdomain VARCHAR DEFAULT NULL,
            p_country   VARCHAR DEFAULT 'IN',
            p_timezone  VARCHAR DEFAULT 'Asia/Kolkata',
            p_currency  VARCHAR DEFAULT 'INR'
        ) RETURNS UUID
        LANGUAGE plpgsql
        AS $$
        DECLARE
            v_id UUID;
        BEGIN
            v_id := gen_random_uuid();
            INSERT INTO platform.tenants (
                id, tenant_id, name, slug, subdomain, status, email,
                country, timezone, currency
            ) VALUES (
                v_id, v_id, p_name, p_slug, COALESCE(p_subdomain, p_slug), 'trial', p_email,
                p_country, p_timezone, p_currency
            );
            RETURN v_id;
        END;
        $$
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS platform.create_tenant(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR)")
    op.execute("DROP TABLE IF EXISTS platform.tenant_settings CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.tenant_locations CASCADE")
    op.execute(
        """
        ALTER TABLE platform.tenants
            DROP COLUMN IF EXISTS logo_url,
            DROP COLUMN IF EXISTS address_line1,
            DROP COLUMN IF EXISTS address_line2,
            DROP COLUMN IF EXISTS city,
            DROP COLUMN IF EXISTS state,
            DROP COLUMN IF EXISTS postal_code,
            DROP COLUMN IF EXISTS tax_registration_no
        """
    )
