"""MVP-077 — patient consent_method column for FR-PAT-009.

Revision ID: 023_patient_consent_method
Revises: 022_generate_mrn_function
"""

from collections.abc import Sequence

from alembic import op

revision: str = "023_patient_consent_method"
down_revision: str | None = "022_generate_mrn_function"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE core.patients
            ADD COLUMN consent_method VARCHAR(20)
                CHECK (consent_method IS NULL OR consent_method IN ('written', 'verbal', 'digital'))
        """
    )
    op.execute(
        "COMMENT ON COLUMN core.patients.consent_method IS "
        "'How data-processing consent was obtained (written, verbal, digital).'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE core.patients DROP COLUMN IF EXISTS consent_method")
