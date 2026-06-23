"""MVP-060 — catalog-only revision (permissions seeded via RbacProvisioner).

Revision ID: 019_permission_catalog_s6
Revises: 018_org_tables
"""

from collections.abc import Sequence

from alembic import op

revision: str = "019_permission_catalog_s6"
down_revision: str | None = "018_org_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op: admin:departments is provisioned from PERMISSION_CATALOG on tenant setup."""
    pass


def downgrade() -> None:
    pass
