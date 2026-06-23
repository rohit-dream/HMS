"""MVP-044 — allow past_due on platform.tenants.status.

Revision ID: 017_tenant_status_past_due
Revises: 016_permission_catalog_seed
"""

from collections.abc import Sequence

from alembic import op

revision: str = "017_tenant_status_past_due"
down_revision: str | None = "016_permission_catalog_seed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE platform.tenants DROP CONSTRAINT IF EXISTS tenants_status_check")
    op.execute(
        """
        ALTER TABLE platform.tenants
            ADD CONSTRAINT tenants_status_check
            CHECK (status IN ('trial', 'active', 'past_due', 'suspended', 'cancelled'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE platform.tenants DROP CONSTRAINT IF EXISTS tenants_status_check")
    op.execute(
        """
        ALTER TABLE platform.tenants
            ADD CONSTRAINT tenants_status_check
            CHECK (status IN ('trial', 'active', 'suspended', 'cancelled'))
        """
    )
