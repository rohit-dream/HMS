"""MVP-091 — clinical OPD tables + RLS + number generators.

Sprint 9 logical migration: 008_opd_tables

Revision ID: 026_opd_tables
Revises: 025_appointment_tables
"""

from collections.abc import Sequence

from alembic import op

from app.db.generate_opd_numbers_sql import (
    GENERATE_OPD_NUMBERS_GRANT_SQL,
    GENERATE_PRESCRIPTION_NUMBER_FUNCTION_SQL,
    GENERATE_VISIT_NUMBER_FUNCTION_SQL,
)
from app.db.rls_policies import (
    CLINICAL_OPD_RLS_TABLES,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "026_opd_tables"
down_revision: str | None = "025_appointment_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OPD_TABLES_IN_DROP_ORDER: tuple[str, ...] = (
    "opd_referrals",
    "opd_prescription_items",
    "opd_prescriptions",
    "opd_clinical_notes",
    "opd_vitals",
    "opd_queue",
    "opd_visits",
)


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE clinical.opd_visits (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
            visit_number        VARCHAR(20) NOT NULL,
            patient_id          UUID NOT NULL,
            doctor_id           UUID NOT NULL,
            appointment_id      UUID,
            location_id         UUID,
            visit_date          DATE NOT NULL,
            visit_type          VARCHAR(20) NOT NULL
                                CHECK (visit_type IN ('walk_in', 'appointment')),
            status              VARCHAR(20) NOT NULL DEFAULT 'waiting'
                                CHECK (status IN (
                                    'waiting', 'in_consultation', 'completed', 'cancelled'
                                )),
            token_number        INTEGER,
            chief_complaint     TEXT,
            started_at          TIMESTAMPTZ,
            completed_at        TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by          UUID,
            updated_at          TIMESTAMPTZ,
            updated_by          UUID,
            deleted_at          TIMESTAMPTZ,
            deleted_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("COMMENT ON TABLE clinical.opd_visits IS 'Outpatient department encounters.'")
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_visits_tenant_id_id "
        "ON clinical.opd_visits (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_visits
            ADD CONSTRAINT fk_opd_visits_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_visits
            ADD CONSTRAINT fk_opd_visits_doctor
            FOREIGN KEY (tenant_id, doctor_id)
            REFERENCES core.doctors (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_visits
            ADD CONSTRAINT fk_opd_visits_appointment
            FOREIGN KEY (tenant_id, appointment_id)
            REFERENCES clinical.appointments (tenant_id, id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_visits
            ADD CONSTRAINT fk_opd_visits_location
            FOREIGN KEY (tenant_id, location_id)
            REFERENCES platform.tenant_locations (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_visits_tenant_number "
        "ON clinical.opd_visits (tenant_id, visit_number)"
    )
    op.execute(
        """
        CREATE INDEX idx_opd_visits_doctor_date
        ON clinical.opd_visits (tenant_id, doctor_id, visit_date)
        """
    )
    op.execute(
        "CREATE INDEX idx_opd_visits_patient ON clinical.opd_visits (tenant_id, patient_id)"
    )
    op.execute("CREATE INDEX idx_opd_visits_tenant_id ON clinical.opd_visits (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_opd_visits_tenant_active
        ON clinical.opd_visits (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_opd_visits_tenant_appointment_active
        ON clinical.opd_visits (tenant_id, appointment_id)
        WHERE appointment_id IS NOT NULL
          AND deleted_at IS NULL
          AND status <> 'cancelled'
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_visits_updated_at BEFORE UPDATE ON clinical.opd_visits
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE clinical.opd_queue (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
            opd_visit_id        UUID NOT NULL,
            doctor_id           UUID NOT NULL,
            token_number        INTEGER NOT NULL,
            queue_date          DATE NOT NULL,
            status              VARCHAR(20) NOT NULL DEFAULT 'waiting'
                                CHECK (status IN (
                                    'waiting', 'called', 'in_consultation', 'completed', 'skipped'
                                )),
            priority            VARCHAR(10) NOT NULL DEFAULT 'normal'
                                CHECK (priority IN ('normal', 'urgent')),
            called_at           TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by          UUID,
            updated_at          TIMESTAMPTZ,
            updated_by          UUID,
            deleted_at          TIMESTAMPTZ,
            deleted_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("COMMENT ON TABLE clinical.opd_queue IS 'OPD token queue per doctor.'")
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_queue_tenant_id_id ON clinical.opd_queue (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_queue
            ADD CONSTRAINT fk_opd_queue_visit
            FOREIGN KEY (tenant_id, opd_visit_id)
            REFERENCES clinical.opd_visits (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_queue
            ADD CONSTRAINT fk_opd_queue_doctor
            FOREIGN KEY (tenant_id, doctor_id)
            REFERENCES core.doctors (tenant_id, id)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_opd_queue_doctor_date
        ON clinical.opd_queue (tenant_id, doctor_id, queue_date, status)
        """
    )
    op.execute("CREATE INDEX idx_opd_queue_tenant_id ON clinical.opd_queue (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_opd_queue_tenant_active
        ON clinical.opd_queue (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_opd_queue_active_visit
        ON clinical.opd_queue (tenant_id, opd_visit_id)
        WHERE deleted_at IS NULL
          AND status NOT IN ('completed', 'skipped')
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_queue_updated_at BEFORE UPDATE ON clinical.opd_queue
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE clinical.opd_vitals (
            id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id                UUID NOT NULL REFERENCES platform.tenants(id),
            opd_visit_id             UUID NOT NULL,
            recorded_at              TIMESTAMPTZ NOT NULL,
            blood_pressure_systolic  SMALLINT,
            blood_pressure_diastolic SMALLINT,
            pulse_rate               SMALLINT,
            temperature              DECIMAL(4,1),
            respiratory_rate         SMALLINT,
            spo2                     SMALLINT,
            weight_kg                DECIMAL(5,2),
            height_cm                DECIMAL(5,1),
            bmi                      DECIMAL(4,1),
            notes                    TEXT,
            created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by               UUID,
            updated_at               TIMESTAMPTZ,
            updated_by               UUID,
            deleted_at               TIMESTAMPTZ,
            deleted_by               UUID,
            version                  INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE clinical.opd_vitals IS 'Vital signs recorded during OPD visits.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_vitals_tenant_id_id ON clinical.opd_vitals (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_vitals
            ADD CONSTRAINT fk_opd_vitals_visit
            FOREIGN KEY (tenant_id, opd_visit_id)
            REFERENCES clinical.opd_visits (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE INDEX idx_opd_vitals_tenant_id ON clinical.opd_vitals (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_opd_vitals_tenant_active
        ON clinical.opd_vitals (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_vitals_updated_at BEFORE UPDATE ON clinical.opd_vitals
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE clinical.opd_clinical_notes (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            opd_visit_id    UUID NOT NULL,
            note_type       VARCHAR(30) NOT NULL
                            CHECK (note_type IN ('examination', 'diagnosis', 'plan', 'general')),
            content         TEXT NOT NULL,
            icd_code        VARCHAR(10),
            icd_description VARCHAR(255),
            is_final        BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE clinical.opd_clinical_notes IS "
        "'Consultation notes and diagnosis for OPD visits.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_clinical_notes_tenant_id_id "
        "ON clinical.opd_clinical_notes (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_clinical_notes
            ADD CONSTRAINT fk_opd_clinical_notes_visit
            FOREIGN KEY (tenant_id, opd_visit_id)
            REFERENCES clinical.opd_visits (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_opd_clinical_notes_tenant_id ON clinical.opd_clinical_notes (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_opd_clinical_notes_tenant_active
        ON clinical.opd_clinical_notes (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_clinical_notes_updated_at
            BEFORE UPDATE ON clinical.opd_clinical_notes
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE clinical.opd_prescriptions (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
            opd_visit_id        UUID NOT NULL,
            patient_id          UUID NOT NULL,
            doctor_id           UUID NOT NULL,
            prescription_number VARCHAR(20) NOT NULL,
            prescribed_at       TIMESTAMPTZ NOT NULL,
            status              VARCHAR(20) NOT NULL DEFAULT 'active'
                                CHECK (status IN (
                                    'active', 'dispensed', 'partially_dispensed', 'cancelled'
                                )),
            notes               TEXT,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by          UUID,
            updated_at          TIMESTAMPTZ,
            updated_by          UUID,
            deleted_at          TIMESTAMPTZ,
            deleted_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("COMMENT ON TABLE clinical.opd_prescriptions IS 'OPD prescription headers.'")
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_prescriptions_tenant_id_id "
        "ON clinical.opd_prescriptions (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_prescriptions
            ADD CONSTRAINT fk_opd_rx_visit
            FOREIGN KEY (tenant_id, opd_visit_id)
            REFERENCES clinical.opd_visits (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_prescriptions
            ADD CONSTRAINT fk_opd_rx_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_prescriptions
            ADD CONSTRAINT fk_opd_rx_doctor
            FOREIGN KEY (tenant_id, doctor_id)
            REFERENCES core.doctors (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_prescriptions_number "
        "ON clinical.opd_prescriptions (tenant_id, prescription_number)"
    )
    op.execute(
        "CREATE INDEX idx_opd_prescriptions_tenant_id ON clinical.opd_prescriptions (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_opd_prescriptions_tenant_active
        ON clinical.opd_prescriptions (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_prescriptions_updated_at
            BEFORE UPDATE ON clinical.opd_prescriptions
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE clinical.opd_prescription_items (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            prescription_id UUID NOT NULL,
            medicine_id     UUID,
            medicine_name   VARCHAR(255) NOT NULL,
            dosage          VARCHAR(100) NOT NULL,
            frequency       VARCHAR(100) NOT NULL,
            duration        VARCHAR(100) NOT NULL,
            route           VARCHAR(50),
            instructions    TEXT,
            quantity        INTEGER CHECK (quantity IS NULL OR quantity > 0),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE clinical.opd_prescription_items IS 'Line items on OPD prescriptions.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_prescription_items_tenant_id_id "
        "ON clinical.opd_prescription_items (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_prescription_items
            ADD CONSTRAINT fk_opd_rx_items_rx
            FOREIGN KEY (tenant_id, prescription_id)
            REFERENCES clinical.opd_prescriptions (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_opd_prescription_items_tenant_id "
        "ON clinical.opd_prescription_items (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_opd_prescription_items_tenant_active
        ON clinical.opd_prescription_items (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_prescription_items_updated_at
            BEFORE UPDATE ON clinical.opd_prescription_items
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE clinical.opd_referrals (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
            opd_visit_id        UUID NOT NULL,
            patient_id          UUID NOT NULL,
            referring_doctor_id UUID NOT NULL,
            referred_doctor_id  UUID,
            referral_type       VARCHAR(20) NOT NULL
                                CHECK (referral_type IN ('internal', 'external')),
            external_facility   VARCHAR(255),
            reason              TEXT NOT NULL,
            urgency             VARCHAR(10) NOT NULL DEFAULT 'routine'
                                CHECK (urgency IN ('routine', 'urgent', 'emergency')),
            status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending', 'accepted', 'completed')),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by          UUID,
            updated_at          TIMESTAMPTZ,
            updated_by          UUID,
            deleted_at          TIMESTAMPTZ,
            deleted_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE clinical.opd_referrals IS "
        "'Internal and external referrals from OPD visits.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_opd_referrals_tenant_id_id ON clinical.opd_referrals (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_referrals
            ADD CONSTRAINT fk_opd_referrals_visit
            FOREIGN KEY (tenant_id, opd_visit_id)
            REFERENCES clinical.opd_visits (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_referrals
            ADD CONSTRAINT fk_opd_referrals_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_referrals
            ADD CONSTRAINT fk_opd_referrals_referring
            FOREIGN KEY (tenant_id, referring_doctor_id)
            REFERENCES core.doctors (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE clinical.opd_referrals
            ADD CONSTRAINT fk_opd_referrals_referred
            FOREIGN KEY (tenant_id, referred_doctor_id)
            REFERENCES core.doctors (tenant_id, id)
        """
    )
    op.execute("CREATE INDEX idx_opd_referrals_tenant_id ON clinical.opd_referrals (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_opd_referrals_tenant_active
        ON clinical.opd_referrals (tenant_id) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opd_referrals_updated_at BEFORE UPDATE ON clinical.opd_referrals
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    for table in CLINICAL_OPD_RLS_TABLES:
        for stmt in enable_rls_statements("clinical", table):
            op.execute(stmt)
        for stmt in tenant_isolation_policy_statements("clinical", table):
            op.execute(stmt)

    op.execute(GENERATE_VISIT_NUMBER_FUNCTION_SQL)
    op.execute(GENERATE_PRESCRIPTION_NUMBER_FUNCTION_SQL)
    op.execute(GENERATE_OPD_NUMBERS_GRANT_SQL)

    for table in CLINICAL_OPD_RLS_TABLES:
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON clinical.{table} TO hms_app"
        )


def downgrade() -> None:
    op.execute("REVOKE EXECUTE ON FUNCTION clinical.generate_prescription_number(UUID) FROM hms_app")
    op.execute("REVOKE EXECUTE ON FUNCTION clinical.generate_visit_number(UUID) FROM hms_app")
    op.execute("DROP FUNCTION IF EXISTS clinical.generate_prescription_number(UUID)")
    op.execute("DROP FUNCTION IF EXISTS clinical.generate_visit_number(UUID)")

    for table in reversed(CLINICAL_OPD_RLS_TABLES):
        for stmt in disable_rls_statements("clinical", table):
            op.execute(stmt)

    for table in _OPD_TABLES_IN_DROP_ORDER:
        op.execute(f"DROP TABLE IF EXISTS clinical.{table} CASCADE")
