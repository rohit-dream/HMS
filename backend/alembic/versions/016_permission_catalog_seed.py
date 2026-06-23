"""MVP-037 — sync permission catalog (opd:queue, admin:staff) to all tenants.

Revision ID: 016_permission_catalog_seed
Revises: 015_rbac_invite_rls
"""

from collections.abc import Sequence

from alembic import op

revision: str = "016_permission_catalog_seed"
down_revision: str | None = "015_rbac_invite_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from app.core.database import session_scope
    from app.domains.identity.services.rbac_service import RbacProvisioner

    with session_scope() as db:
        RbacProvisioner(db).sync_catalog_for_all_tenants()
        db.commit()


def downgrade() -> None:
    """Catalog permissions are additive; downgrade is a no-op."""
