-- Patient search indexes (applied via Alembic 021_patient_search_indexes).
-- Requires: core.patients (020_patient_tables), pg_trgm extension.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_patients_tenant_phone
    ON core.patients (tenant_id, phone)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_patients_name_search
    ON core.patients (tenant_id, first_name, last_name)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_patients_name_trgm
    ON core.patients
    USING GIN ((first_name || ' ' || COALESCE(last_name, '')) gin_trgm_ops)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_patients_phone_trgm
    ON core.patients
    USING GIN (phone gin_trgm_ops)
    WHERE deleted_at IS NULL;

-- MRN exact lookup: uq_patients_tenant_mrn (tenant_id, mrn) from 020_patient_tables.
