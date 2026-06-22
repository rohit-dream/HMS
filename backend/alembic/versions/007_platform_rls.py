"""Platform schema RLS policies — MVP-012.

Enables FORCE ROW LEVEL SECURITY on all five MVP platform tables.
Updates platform.create_tenant() and adds platform.lookup_tenant_for_login()
as SECURITY DEFINER so provisioning and login work without tenant context.

Revision ID: 007_platform_rls
Revises: 006_platform_subscription_tables
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    PLATFORM_RLS_TABLES,
    SUBSCRIPTION_PLANS_SELECT_USING,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "007_platform_rls"
down_revision: str | None = "006_platform_subscription_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CREATE_TENANT_SECURITY_DEFINER = """
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
SECURITY DEFINER
SET search_path = platform, public
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
$$;
"""

_LOOKUP_TENANT_FOR_LOGIN = """
CREATE OR REPLACE FUNCTION platform.lookup_tenant_for_login(p_identifier VARCHAR)
RETURNS TABLE (
    id          UUID,
    tenant_id   UUID,
    name        VARCHAR(255),
    slug        VARCHAR(100),
    subdomain   VARCHAR(100),
    status      VARCHAR(20),
    email       VARCHAR(255),
    deleted_at  TIMESTAMPTZ
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = platform, public
STABLE
AS $$
    SELECT
        t.id,
        t.tenant_id,
        t.name,
        t.slug,
        t.subdomain,
        t.status,
        t.email,
        t.deleted_at
    FROM platform.tenants t
    WHERE t.deleted_at IS NULL
      AND (
          lower(t.slug) = lower(p_identifier)
          OR lower(t.subdomain) = lower(p_identifier)
      )
    LIMIT 1;
$$;
"""


def upgrade() -> None:
    for table in PLATFORM_RLS_TABLES:
        for statement in enable_rls_statements("platform", table):
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

    op.execute(_CREATE_TENANT_SECURITY_DEFINER)
    op.execute(_LOOKUP_TENANT_FOR_LOGIN)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS platform.lookup_tenant_for_login(VARCHAR)")
    op.execute(
        "DROP FUNCTION IF EXISTS platform.create_tenant("
        "VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR)"
    )

    for table in reversed(PLATFORM_RLS_TABLES):
        for statement in disable_rls_statements("platform", table):
            op.execute(statement)

    # Restore non-SECURITY DEFINER create_tenant from 004_platform_hospital.
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
        $$;
        """
    )
