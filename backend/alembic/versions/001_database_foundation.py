"""Database foundation — extensions, schemas, shared trigger functions.

No business tables in this revision (per DATABASE_DESIGN.md §1.4).
Business tables follow in subsequent migrations (Phase 1: platform + core RBAC).

Revision ID: 001_database_foundation
Revises:
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_database_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMAS: tuple[str, ...] = (
    "platform",
    "core",
    "clinical",
    "billing",
    "pharmacy",
    "laboratory",
    "comms",
    "audit",
)

SET_UPDATED_AT_FUNCTION = """
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

ENFORCE_TENANT_SELF_REFERENCE_FUNCTION = """
CREATE OR REPLACE FUNCTION platform.enforce_tenant_self_reference()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tenant_id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'platform.tenants.tenant_id must equal id';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.execute(SET_UPDATED_AT_FUNCTION)
    op.execute(ENFORCE_TENANT_SELF_REFERENCE_FUNCTION)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS platform.enforce_tenant_self_reference()")
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at()")

    for schema in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
