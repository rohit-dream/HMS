"""MVP-071 — core.generate_mrn() per-tenant MRN-YYYY-NNNNN generator.

Revision ID: 022_generate_mrn_function
Revises: 021_patient_search_indexes
"""

from collections.abc import Sequence

from alembic import op

from app.db.generate_mrn_sql import GENERATE_MRN_FUNCTION_SQL, GENERATE_MRN_GRANT_SQL

revision: str = "022_generate_mrn_function"
down_revision: str | None = "021_patient_search_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(GENERATE_MRN_FUNCTION_SQL)
    op.execute(GENERATE_MRN_GRANT_SQL)


def downgrade() -> None:
    op.execute("REVOKE EXECUTE ON FUNCTION core.generate_mrn(UUID) FROM hms_app")
    op.execute("DROP FUNCTION IF EXISTS core.generate_mrn(UUID)")
