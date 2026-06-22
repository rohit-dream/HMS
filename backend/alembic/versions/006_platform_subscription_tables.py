"""Platform subscription tables — subscription_plans, tenant_subscriptions.

Completes MVP-011 platform table set (Sprint 2).
Tables tenants, tenant_locations, tenant_settings were added in 002_auth_tables / 004_platform_hospital.

Revision ID: 006_platform_subscription_tables
Revises: 005_password_reset_tokens
"""

from collections.abc import Sequence

from alembic import op

revision: str = "006_platform_subscription_tables"
down_revision: str | None = "005_password_reset_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Backfill tenant root indexes from DATABASE_DESIGN.md (safe if already present).
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_tenants_tenant_id_id ON platform.tenants (tenant_id, id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_tenants_tenant_id ON platform.tenants (tenant_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenants_tenant_active
        ON platform.tenants (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE platform.subscription_plans (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            code            VARCHAR(50) NOT NULL,
            name            VARCHAR(100) NOT NULL,
            description     TEXT,
            price_monthly   DECIMAL(12,2) NOT NULL CHECK (price_monthly >= 0),
            price_annual    DECIMAL(12,2) CHECK (price_annual IS NULL OR price_annual >= 0),
            max_users       INTEGER NOT NULL CHECK (max_users > 0),
            max_beds        INTEGER CHECK (max_beds IS NULL OR max_beds > 0),
            max_patients    INTEGER CHECK (max_patients IS NULL OR max_patients > 0),
            features        JSONB NOT NULL DEFAULT '{}',
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
        "COMMENT ON TABLE platform.subscription_plans IS "
        "'SaaS subscription plan definitions (seeded under system tenant).'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_subscription_plans_tenant_id_id "
        "ON platform.subscription_plans (tenant_id, id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_subscription_plans_tenant_code "
        "ON platform.subscription_plans (tenant_id, code)"
    )
    op.execute(
        "CREATE INDEX idx_subscription_plans_tenant_id ON platform.subscription_plans (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_subscription_plans_tenant_active
        ON platform.subscription_plans (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_subscription_plans_updated_at BEFORE UPDATE ON platform.subscription_plans
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE platform.tenant_subscriptions (
            id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id                       UUID NOT NULL REFERENCES platform.tenants(id),
            plan_id                         UUID NOT NULL REFERENCES platform.subscription_plans(id),
            status                          VARCHAR(20) NOT NULL DEFAULT 'trial'
                                            CHECK (status IN ('trial', 'active', 'past_due', 'suspended', 'cancelled')),
            billing_cycle                   VARCHAR(10) NOT NULL DEFAULT 'monthly'
                                            CHECK (billing_cycle IN ('monthly', 'annual')),
            trial_ends_at                   TIMESTAMPTZ,
            current_period_start            TIMESTAMPTZ NOT NULL,
            current_period_end              TIMESTAMPTZ NOT NULL,
            cancelled_at                    TIMESTAMPTZ,
            payment_gateway_customer_id     VARCHAR(255),
            payment_gateway_subscription_id VARCHAR(255),
            created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by                      UUID,
            updated_at                      TIMESTAMPTZ,
            updated_by                      UUID,
            deleted_at                      TIMESTAMPTZ,
            deleted_by                      UUID,
            version                         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE platform.tenant_subscriptions IS "
        "'Tenant subscription history and current plan status.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_tenant_subscriptions_tenant_id_id "
        "ON platform.tenant_subscriptions (tenant_id, id)"
    )
    op.execute(
        "CREATE INDEX idx_tenant_subscriptions_tenant_status "
        "ON platform.tenant_subscriptions (tenant_id, status)"
    )
    op.execute(
        "CREATE INDEX idx_tenant_subscriptions_tenant_id "
        "ON platform.tenant_subscriptions (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_tenant_subscriptions_tenant_active
        ON platform.tenant_subscriptions (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_tenant_subscriptions_updated_at BEFORE UPDATE ON platform.tenant_subscriptions
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS platform.tenant_subscriptions CASCADE")
    op.execute("DROP TABLE IF EXISTS platform.subscription_plans CASCADE")
    op.execute("DROP INDEX IF EXISTS platform.idx_tenants_tenant_active")
    op.execute("DROP INDEX IF EXISTS platform.idx_tenants_tenant_id")
    op.execute("DROP INDEX IF EXISTS platform.uq_tenants_tenant_id_id")
