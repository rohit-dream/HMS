"""MVP-069 — core patient tables: patients, allergies, contacts, documents + RLS.

Sprint 7 logical migration: 006_patient_tables

Revision ID: 020_patient_tables
Revises: 019_permission_catalog_s6
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    CORE_PATIENT_RLS_TABLES,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "020_patient_tables"
down_revision: str | None = "019_permission_catalog_s6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE core.patients (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
            mrn                 VARCHAR(20) NOT NULL,
            first_name          VARCHAR(100) NOT NULL,
            last_name           VARCHAR(100),
            date_of_birth       DATE NOT NULL,
            gender              VARCHAR(10) NOT NULL
                                CHECK (gender IN ('male', 'female', 'other')),
            blood_group         VARCHAR(5),
            phone               VARCHAR(20) NOT NULL,
            email               VARCHAR(255),
            address_line1       VARCHAR(255),
            city                VARCHAR(100),
            state               VARCHAR(100),
            postal_code         VARCHAR(20),
            photo_url           TEXT,
            id_proof_type       VARCHAR(50),
            id_proof_number     VARCHAR(50),
            marital_status      VARCHAR(20),
            occupation          VARCHAR(100),
            consent_given_at    TIMESTAMPTZ,
            location_id         UUID,
            chronic_conditions  JSONB NOT NULL DEFAULT '[]'::jsonb,
            metadata            JSONB,
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
        "COMMENT ON TABLE core.patients IS 'Patient demographics and medical record number.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_patients_tenant_id_id ON core.patients (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.patients
            ADD CONSTRAINT fk_patients_location
            FOREIGN KEY (tenant_id, location_id)
            REFERENCES platform.tenant_locations (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_patients_tenant_mrn ON core.patients (tenant_id, mrn)"
    )
    op.execute("CREATE INDEX idx_patients_tenant_id ON core.patients (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_patients_tenant_active
        ON core.patients (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE core.patient_allergies (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            patient_id      UUID NOT NULL,
            allergen        VARCHAR(255) NOT NULL,
            severity        VARCHAR(20) NOT NULL
                            CHECK (severity IN ('mild', 'moderate', 'severe')),
            reaction        TEXT,
            onset_date      DATE,
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
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
    op.execute("COMMENT ON TABLE core.patient_allergies IS 'Patient allergy records.'")
    op.execute(
        "CREATE UNIQUE INDEX uq_patient_allergies_tenant_id_id "
        "ON core.patient_allergies (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.patient_allergies
            ADD CONSTRAINT fk_patient_allergies_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_patient_allergies_tenant_id ON core.patient_allergies (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_patient_allergies_tenant_active
        ON core.patient_allergies (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE core.patient_contacts (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            patient_id      UUID NOT NULL,
            name            VARCHAR(200) NOT NULL,
            relationship    VARCHAR(50) NOT NULL,
            phone           VARCHAR(20) NOT NULL,
            email           VARCHAR(255),
            is_emergency    BOOLEAN NOT NULL DEFAULT FALSE,
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
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
        "COMMENT ON TABLE core.patient_contacts IS "
        "'Emergency and guardian contacts for patients.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_patient_contacts_tenant_id_id "
        "ON core.patient_contacts (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.patient_contacts
            ADD CONSTRAINT fk_patient_contacts_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_patient_contacts_tenant_id ON core.patient_contacts (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_patient_contacts_tenant_active
        ON core.patient_contacts (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE core.patient_documents (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            patient_id      UUID NOT NULL,
            document_type   VARCHAR(50) NOT NULL
                            CHECK (document_type IN ('id_proof', 'consent', 'report', 'other')),
            file_name       VARCHAR(255) NOT NULL,
            file_path       TEXT NOT NULL,
            file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes >= 0),
            mime_type       VARCHAR(100) NOT NULL,
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
        "COMMENT ON TABLE core.patient_documents IS "
        "'Attached patient documents and consents.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_patient_documents_tenant_id_id "
        "ON core.patient_documents (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.patient_documents
            ADD CONSTRAINT fk_patient_documents_patient
            FOREIGN KEY (tenant_id, patient_id)
            REFERENCES core.patients (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX idx_patient_documents_tenant_id ON core.patient_documents (tenant_id)"
    )
    op.execute(
        """
        CREATE INDEX idx_patient_documents_tenant_active
        ON core.patient_documents (tenant_id) WHERE deleted_at IS NULL
        """
    )

    for table in ("patients", "patient_allergies", "patient_contacts", "patient_documents"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at BEFORE UPDATE ON core.{table}
                FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
            """
        )

    for table in CORE_PATIENT_RLS_TABLES:
        for stmt in enable_rls_statements("core", table):
            op.execute(stmt)
        for stmt in tenant_isolation_policy_statements("core", table):
            op.execute(stmt)

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO hms_app"
    )


def downgrade() -> None:
    for table in reversed(CORE_PATIENT_RLS_TABLES):
        for stmt in disable_rls_statements("core", table):
            op.execute(stmt)

    op.execute("DROP TABLE IF EXISTS core.patient_documents CASCADE")
    op.execute("DROP TABLE IF EXISTS core.patient_contacts CASCADE")
    op.execute("DROP TABLE IF EXISTS core.patient_allergies CASCADE")
    op.execute("DROP TABLE IF EXISTS core.patients CASCADE")
