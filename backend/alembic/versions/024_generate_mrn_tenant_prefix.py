"""MVP-071 follow-up — core.generate_mrn() reads tenant clinical.mrn_prefix setting.

Revision ID: 024_generate_mrn_tenant_prefix
Revises: 023_patient_consent_method
"""

from collections.abc import Sequence

from alembic import op

from app.db.generate_mrn_sql import GENERATE_MRN_FUNCTION_SQL, GENERATE_MRN_GRANT_SQL

revision: str = "024_generate_mrn_tenant_prefix"
down_revision: str | None = "023_patient_consent_method"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(GENERATE_MRN_FUNCTION_SQL)
    op.execute(GENERATE_MRN_GRANT_SQL)


def downgrade() -> None:
    op.execute("REVOKE EXECUTE ON FUNCTION core.generate_mrn(UUID) FROM hms_app")
    op.execute("DROP FUNCTION IF EXISTS core.generate_mrn(UUID)")
