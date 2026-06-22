"""Seed system tenant and subscription plan catalog — MVP-015.

Revision ID: 011_system_tenant_plans_seed
Revises: 010_create_tenant_function
"""

from collections.abc import Sequence

from alembic import op

from app.db.platform_seed_sql import (
    subscription_plans_seed_downgrade_sql,
    subscription_plans_seed_sql,
    system_tenant_seed_sql,
)

revision: str = "011_system_tenant_plans_seed"
down_revision: str | None = "010_create_tenant_function"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(system_tenant_seed_sql())
    op.execute(subscription_plans_seed_sql())


def downgrade() -> None:
    op.execute(subscription_plans_seed_downgrade_sql())
