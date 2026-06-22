"""Production platform.create_tenant() — MVP-013.

Replaces the minimal function from 004/007 with validation, normalization,
reserved-slug checks, and duplicate detection.

Revision ID: 010_create_tenant_function
Revises: 009_rls_null_safe_policies
"""

from collections.abc import Sequence

from alembic import op

from app.db.create_tenant_sql import CREATE_TENANT_FUNCTION_SQL

revision: str = "010_create_tenant_function"
down_revision: str | None = "009_rls_null_safe_policies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(CREATE_TENANT_FUNCTION_SQL)


def downgrade() -> None:
    # Restore SECURITY DEFINER function from 007 (without validation extras).
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
    )
