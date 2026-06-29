"""MVP-083 — clinical.appointments table + RLS.

Sprint 8 logical migration: 007_appointment_tables

Revision ID: 025_appointment_tables
Revises: 024_generate_mrn_tenant_prefix
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    CLINICAL_APPOINTMENT_RLS_TABLES,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "025_appointment_tables"
down_revision: str | None = "024_generate_mrn_tenant_prefix"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE clinical.appointments (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
            patient_id          UUID NOT NULL,
            doctor_id           UUID NOT NULL,
            location_id         UUID,
            appointment_date    DATE NOT NULL,
            start_time          TIME NOT NULL,
            end_time            TIME NOT NULL,
            appointment_type    VARCHAR(20) NOT NULL
                                CHECK (appointment_type IN ('new', 'follow_up', 'emergency')),
            status              VARCHAR(20) NOT NULL DEFAULT 'scheduled'
                                CHECK (status IN (
                                    'scheduled', 'confirmed', 'completed', 'cancelled', 'no_show'
                                )),
            is_walk_in          BOOLEAN NOT NULL DEFAULT FALSE,
            notes               TEXT,
            cancelled_reason    TEXT,
            reminder_sent_at    TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by          UUID,
            updated_at          TIMESTAMPTZ,
            updated_by          UUID,
            deleted_at          TIMESTAMPTZ,
            deleted_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1,
            CHECK (end_time > start_time)
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE clinical.appointments IS 'Scheduled patient appointments.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_appointments_tenant_id_id "
        "ON clinical.appointments (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.appointments
            ADD CONSTRAINT fk_appointments_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.appointments
            ADD CONSTRAINT fk_appointments_doctor
            FOREIGN KEY (tenant_id, doctor_id)
            REFERENCES core.doctors (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.appointments
            ADD CONSTRAINT fk_appointments_location
            FOREIGN KEY (tenant_id, location_id)
            REFERENCES platform.tenant_locations (tenant_id, id)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_appointments_doctor_date
        ON clinical.appointments (tenant_id, doctor_id, appointment_date)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_appointments_patient
        ON clinical.appointments (tenant_id, patient_id)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_appointments_status_date
        ON clinical.appointments (tenant_id, status, appointment_date)
        """
    )
    op.execute("CREATE INDEX idx_appointments_tenant_id ON clinical.appointments (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_appointments_tenant_active
        ON clinical.appointments (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_appointments_doctor_slot_active
        ON clinical.appointments (tenant_id, doctor_id, appointment_date, start_time)
        WHERE deleted_at IS NULL
          AND status NOT IN ('cancelled', 'no_show')
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_appointments_updated_at BEFORE UPDATE ON clinical.appointments
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    for table in CLINICAL_APPOINTMENT_RLS_TABLES:
        for stmt in enable_rls_statements("clinical", table):
            op.execute(stmt)
        for stmt in tenant_isolation_policy_statements("clinical", table):
            op.execute(stmt)

    op.execute("GRANT USAGE ON SCHEMA clinical TO hms_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA clinical TO hms_app"
    )


def downgrade() -> None:
    for table in reversed(CLINICAL_APPOINTMENT_RLS_TABLES):
        for stmt in disable_rls_statements("clinical", table):
            op.execute(stmt)

    op.execute("DROP TABLE IF EXISTS clinical.appointments CASCADE")
