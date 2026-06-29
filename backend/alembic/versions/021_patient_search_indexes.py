"""MVP-070 — pg_trgm extension and patient search indexes.

Sprint 7 logical migration: 006_patient_search_indexes

Revision ID: 021_patient_search_indexes
Revises: 020_patient_tables
"""

from collections.abc import Sequence

from alembic import op

revision: str = "021_patient_search_indexes"
down_revision: str | None = "020_patient_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Partial filter: active patients only (soft-deleted rows excluded from search).
_ACTIVE_PATIENTS = "deleted_at IS NULL"

# Expression for full-name fuzzy search (pg_trgm).
_PATIENT_FULL_NAME_EXPR = "(first_name || ' ' || COALESCE(last_name, ''))"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        f"""
        CREATE INDEX idx_patients_tenant_phone
        ON core.patients (tenant_id, phone)
        WHERE {_ACTIVE_PATIENTS}
        """
    )
    op.execute(
        f"""
        CREATE INDEX idx_patients_name_search
        ON core.patients (tenant_id, first_name, last_name)
        WHERE {_ACTIVE_PATIENTS}
        """
    )
    op.execute(
        f"""
        CREATE INDEX idx_patients_name_trgm
        ON core.patients
        USING GIN ({_PATIENT_FULL_NAME_EXPR} gin_trgm_ops)
        WHERE {_ACTIVE_PATIENTS}
        """
    )
    op.execute(
        f"""
        CREATE INDEX idx_patients_phone_trgm
        ON core.patients
        USING GIN (phone gin_trgm_ops)
        WHERE {_ACTIVE_PATIENTS}
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS core.idx_patients_phone_trgm")
    op.execute("DROP INDEX IF EXISTS core.idx_patients_name_trgm")
    op.execute("DROP INDEX IF EXISTS core.idx_patients_name_search")
    op.execute("DROP INDEX IF EXISTS core.idx_patients_tenant_phone")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
