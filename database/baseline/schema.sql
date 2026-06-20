-- =============================================================================
-- Hospital Management SaaS — PostgreSQL Schema
-- Multi-tenant · Shared database · tenant_id row isolation
-- Source: DATABASE_DESIGN.md | PostgreSQL 14+ | 61 tables · 8 schemas
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS platform;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS clinical;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS pharmacy;
CREATE SCHEMA IF NOT EXISTS laboratory;
CREATE SCHEMA IF NOT EXISTS comms;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION platform.enforce_tenant_self_reference()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tenant_id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'platform.tenants.tenant_id must equal id';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PLATFORM SCHEMA
-- =============================================================================
CREATE TABLE platform.tenants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL,
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) NOT NULL,
    subdomain           VARCHAR(100),
    status              VARCHAR(20) NOT NULL DEFAULT 'trial'
                        CHECK (status IN ('trial', 'active', 'suspended', 'cancelled')),
    email               VARCHAR(255) NOT NULL,
    phone               VARCHAR(20),
    logo_url            TEXT,
    address_line1       VARCHAR(255),
    address_line2       VARCHAR(255),
    city                VARCHAR(100),
    state               VARCHAR(100),
    country             VARCHAR(100) NOT NULL DEFAULT 'IN',
    postal_code         VARCHAR(20),
    timezone            VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
    currency            VARCHAR(3) NOT NULL DEFAULT 'INR',
    tax_registration_no VARCHAR(50),
    metadata            JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE platform.tenants IS 'Healthcare organization (tenant root); tenant_id must equal id.';
CREATE UNIQUE INDEX uq_tenants_tenant_id_id ON platform.tenants (tenant_id, id);
ALTER TABLE platform.tenants
    ADD CONSTRAINT fk_tenants_tenant_id FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id)
    DEFERRABLE INITIALLY DEFERRED;
CREATE UNIQUE INDEX uq_tenants_slug ON platform.tenants (slug);
CREATE INDEX idx_tenants_status ON platform.tenants (status);
CREATE INDEX idx_tenants_tenant_id ON platform.tenants (tenant_id);
CREATE INDEX idx_tenants_tenant_active ON platform.tenants (tenant_id) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_tenants_self_ref BEFORE INSERT OR UPDATE ON platform.tenants
    FOR EACH ROW EXECUTE FUNCTION platform.enforce_tenant_self_reference();
CREATE TRIGGER trg_tenants_updated_at BEFORE UPDATE ON platform.tenants
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TABLE platform.subscription_plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    code                VARCHAR(50) NOT NULL,
    name                VARCHAR(100) NOT NULL,
    description         TEXT,
    price_monthly       DECIMAL(12,2) NOT NULL CHECK (price_monthly >= 0),
    price_annual        DECIMAL(12,2) CHECK (price_annual IS NULL OR price_annual >= 0),
    max_users           INTEGER NOT NULL CHECK (max_users > 0),
    max_beds            INTEGER CHECK (max_beds IS NULL OR max_beds > 0),
    max_patients        INTEGER CHECK (max_patients IS NULL OR max_patients > 0),
    features            JSONB NOT NULL DEFAULT '{}',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE platform.subscription_plans IS 'SaaS subscription plan definitions (system tenant seed data).';
CREATE UNIQUE INDEX uq_subscription_plans_tenant_id_id ON platform.subscription_plans (tenant_id, id);
CREATE UNIQUE INDEX uq_subscription_plans_tenant_code ON platform.subscription_plans (tenant_id, code);
CREATE INDEX idx_subscription_plans_tenant_id ON platform.subscription_plans (tenant_id);
CREATE INDEX idx_subscription_plans_tenant_active ON platform.subscription_plans (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE platform.tenant_locations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    name                VARCHAR(255) NOT NULL,
    code                VARCHAR(20) NOT NULL,
    is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
    address_line1       VARCHAR(255),
    city                VARCHAR(100),
    state               VARCHAR(100),
    phone               VARCHAR(20),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE platform.tenant_locations IS 'Branches and facilities per tenant.';
CREATE UNIQUE INDEX uq_tenant_locations_tenant_id_id ON platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_tenant_locations_tenant_code ON platform.tenant_locations (tenant_id, code);
CREATE INDEX idx_tenant_locations_tenant_id ON platform.tenant_locations (tenant_id);
CREATE INDEX idx_tenant_locations_tenant_active ON platform.tenant_locations (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE platform.tenant_subscriptions (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    plan_id                         UUID NOT NULL,
    status                          VARCHAR(20) NOT NULL DEFAULT 'trial'
                                    CHECK (status IN ('trial', 'active', 'past_due', 'suspended', 'cancelled')),
    billing_cycle                   VARCHAR(10) NOT NULL DEFAULT 'monthly'
                                    CHECK (billing_cycle IN ('monthly', 'annual')),
    trial_ends_at                   TIMESTAMPTZ,
    current_period_start            TIMESTAMPTZ NOT NULL,
    current_period_end              TIMESTAMPTZ NOT NULL,
    cancelled_at                    TIMESTAMPTZ,
    payment_gateway_customer_id     VARCHAR(255),
    payment_gateway_subscription_id VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE platform.tenant_subscriptions IS 'Tenant subscription history and current plan status.';
CREATE UNIQUE INDEX uq_tenant_subscriptions_tenant_id_id ON platform.tenant_subscriptions (tenant_id, id);
ALTER TABLE platform.tenant_subscriptions
    ADD CONSTRAINT fk_tsub_plan FOREIGN KEY (tenant_id, plan_id)
    REFERENCES platform.subscription_plans (tenant_id, id);
CREATE INDEX idx_tenant_subscriptions_tenant_status ON platform.tenant_subscriptions (tenant_id, status);
CREATE INDEX idx_tenant_subscriptions_tenant_id ON platform.tenant_subscriptions (tenant_id);
CREATE INDEX idx_tenant_subscriptions_tenant_active ON platform.tenant_subscriptions (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE platform.tenant_settings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    setting_key         VARCHAR(100) NOT NULL,
    setting_value       JSONB NOT NULL,
    description         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE platform.tenant_settings IS 'Key-value tenant configuration store.';
CREATE UNIQUE INDEX uq_tenant_settings_tenant_id_id ON platform.tenant_settings (tenant_id, id);
CREATE UNIQUE INDEX uq_tenant_settings_key ON platform.tenant_settings (tenant_id, setting_key);
CREATE INDEX idx_tenant_settings_tenant_id ON platform.tenant_settings (tenant_id);
CREATE INDEX idx_tenant_settings_tenant_active ON platform.tenant_settings (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- CORE SCHEMA — Identity & RBAC
-- =============================================================================
CREATE TABLE core.roles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    name                VARCHAR(100) NOT NULL,
    code                VARCHAR(50) NOT NULL,
    description         TEXT,
    is_system           BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.roles IS 'Tenant-scoped roles for RBAC.';
CREATE UNIQUE INDEX uq_roles_tenant_id_id ON core.roles (tenant_id, id);
CREATE UNIQUE INDEX uq_roles_tenant_code ON core.roles (tenant_id, code);
CREATE UNIQUE INDEX uq_roles_tenant_name ON core.roles (tenant_id, name);
CREATE INDEX idx_roles_tenant_id ON core.roles (tenant_id);
CREATE INDEX idx_roles_tenant_active ON core.roles (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.permissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    code                VARCHAR(100) NOT NULL,
    name                VARCHAR(150) NOT NULL,
    module              VARCHAR(50) NOT NULL,
    description         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.permissions IS 'Permission catalog (system seed and tenant overrides).';
CREATE UNIQUE INDEX uq_permissions_tenant_id_id ON core.permissions (tenant_id, id);
CREATE UNIQUE INDEX uq_permissions_tenant_code ON core.permissions (tenant_id, code);
CREATE INDEX idx_permissions_tenant_id ON core.permissions (tenant_id);
CREATE INDEX idx_permissions_tenant_active ON core.permissions (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.departments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    name                VARCHAR(150) NOT NULL,
    code                VARCHAR(20) NOT NULL,
    head_staff_id       UUID,
    location_id         UUID,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.departments IS 'Hospital departments.';
CREATE UNIQUE INDEX uq_departments_tenant_id_id ON core.departments (tenant_id, id);
ALTER TABLE core.departments
    ADD CONSTRAINT fk_departments_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_departments_tenant_code ON core.departments (tenant_id, code);
CREATE INDEX idx_departments_tenant_id ON core.departments (tenant_id);
CREATE INDEX idx_departments_tenant_active ON core.departments (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.staff (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    employee_code       VARCHAR(20) NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255),
    phone               VARCHAR(20),
    department_id       UUID,
    designation         VARCHAR(100),
    joining_date        DATE NOT NULL,
    leaving_date        DATE,
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'on_leave', 'terminated')),
    location_id         UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.staff IS 'Employee records.';
CREATE UNIQUE INDEX uq_staff_tenant_id_id ON core.staff (tenant_id, id);
ALTER TABLE core.staff
    ADD CONSTRAINT fk_staff_department FOREIGN KEY (tenant_id, department_id)
    REFERENCES core.departments (tenant_id, id);
ALTER TABLE core.staff
    ADD CONSTRAINT fk_staff_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
ALTER TABLE core.departments
    ADD CONSTRAINT fk_departments_head_staff FOREIGN KEY (tenant_id, head_staff_id)
    REFERENCES core.staff (tenant_id, id);
CREATE UNIQUE INDEX uq_staff_tenant_code ON core.staff (tenant_id, employee_code);
CREATE INDEX idx_staff_tenant_id ON core.staff (tenant_id);
CREATE INDEX idx_staff_tenant_active ON core.staff (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    email               VARCHAR(255) NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    phone               VARCHAR(20),
    avatar_url          TEXT,
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'inactive', 'locked')),
    last_login_at       TIMESTAMPTZ,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until        TIMESTAMPTZ,
    email_verified_at   TIMESTAMPTZ,
    staff_id            UUID,
    location_id         UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.users IS 'Authenticated user accounts.';
CREATE UNIQUE INDEX uq_users_tenant_id_id ON core.users (tenant_id, id);
ALTER TABLE core.users
    ADD CONSTRAINT fk_users_staff FOREIGN KEY (tenant_id, staff_id)
    REFERENCES core.staff (tenant_id, id) ON DELETE SET NULL;
ALTER TABLE core.users
    ADD CONSTRAINT fk_users_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_users_tenant_email ON core.users (tenant_id, email);
CREATE INDEX idx_users_tenant_status ON core.users (tenant_id, status);
CREATE INDEX idx_users_tenant_id ON core.users (tenant_id);
CREATE INDEX idx_users_tenant_active ON core.users (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.role_permissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    role_id             UUID NOT NULL,
    permission_id       UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.role_permissions IS 'Role-to-permission mapping.';
CREATE UNIQUE INDEX uq_role_permissions_tenant_id_id ON core.role_permissions (tenant_id, id);
ALTER TABLE core.role_permissions
    ADD CONSTRAINT fk_role_permissions_role FOREIGN KEY (tenant_id, role_id)
    REFERENCES core.roles (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE core.role_permissions
    ADD CONSTRAINT fk_role_permissions_perm FOREIGN KEY (tenant_id, permission_id)
    REFERENCES core.permissions (tenant_id, id);
CREATE UNIQUE INDEX uq_role_permissions ON core.role_permissions (tenant_id, role_id, permission_id);
CREATE INDEX idx_role_permissions_tenant_id ON core.role_permissions (tenant_id);
CREATE INDEX idx_role_permissions_tenant_active ON core.role_permissions (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.user_roles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    user_id             UUID NOT NULL,
    role_id             UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.user_roles IS 'User-to-role mapping.';
CREATE UNIQUE INDEX uq_user_roles_tenant_id_id ON core.user_roles (tenant_id, id);
ALTER TABLE core.user_roles
    ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE core.user_roles
    ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (tenant_id, role_id)
    REFERENCES core.roles (tenant_id, id) ON DELETE CASCADE;
CREATE UNIQUE INDEX uq_user_roles ON core.user_roles (tenant_id, user_id, role_id);
CREATE INDEX idx_user_roles_tenant_id ON core.user_roles (tenant_id);
CREATE INDEX idx_user_roles_tenant_active ON core.user_roles (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.user_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    user_id             UUID NOT NULL,
    refresh_token_hash  VARCHAR(255) NOT NULL,
    ip_address          INET,
    user_agent          TEXT,
    expires_at          TIMESTAMPTZ NOT NULL,
    revoked_at          TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.user_sessions IS 'Active sessions and refresh tokens.';
CREATE UNIQUE INDEX uq_user_sessions_tenant_id_id ON core.user_sessions (tenant_id, id);
ALTER TABLE core.user_sessions
    ADD CONSTRAINT fk_user_sessions_user FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_user_sessions_user ON core.user_sessions (tenant_id, user_id);
CREATE INDEX idx_user_sessions_expires ON core.user_sessions (expires_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_user_sessions_tenant_id ON core.user_sessions (tenant_id);
CREATE INDEX idx_user_sessions_tenant_active ON core.user_sessions (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.password_reset_tokens (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    user_id             UUID NOT NULL,
    token_hash          VARCHAR(255) NOT NULL,
    expires_at          TIMESTAMPTZ NOT NULL,
    used_at             TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.password_reset_tokens IS 'Password reset workflow tokens.';
CREATE UNIQUE INDEX uq_password_reset_tokens_tenant_id_id ON core.password_reset_tokens (tenant_id, id);
ALTER TABLE core.password_reset_tokens
    ADD CONSTRAINT fk_password_reset_user FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_password_reset_tokens_tenant_id ON core.password_reset_tokens (tenant_id);
CREATE INDEX idx_password_reset_tokens_tenant_active ON core.password_reset_tokens (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- CORE SCHEMA — Patients & Staff
-- =============================================================================
CREATE TABLE core.patients (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    mrn                 VARCHAR(20) NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100),
    date_of_birth       DATE NOT NULL,
    gender              VARCHAR(10) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
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
    metadata            JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.patients IS 'Patient demographics and medical record number.';
CREATE UNIQUE INDEX uq_patients_tenant_id_id ON core.patients (tenant_id, id);
ALTER TABLE core.patients
    ADD CONSTRAINT fk_patients_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_patients_tenant_mrn ON core.patients (tenant_id, mrn);
CREATE INDEX idx_patients_tenant_phone ON core.patients (tenant_id, phone);
CREATE INDEX idx_patients_name_search ON core.patients (tenant_id, first_name, last_name);
CREATE INDEX idx_patients_name_gin ON core.patients USING GIN (to_tsvector('simple', first_name || ' ' || COALESCE(last_name, '')));
CREATE INDEX idx_patients_tenant_id ON core.patients (tenant_id);
CREATE INDEX idx_patients_tenant_active ON core.patients (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.patient_allergies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    patient_id          UUID NOT NULL,
    allergen            VARCHAR(255) NOT NULL,
    severity            VARCHAR(20) NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe')),
    reaction            TEXT,
    onset_date          DATE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.patient_allergies IS 'Patient allergy records.';
CREATE UNIQUE INDEX uq_patient_allergies_tenant_id_id ON core.patient_allergies (tenant_id, id);
ALTER TABLE core.patient_allergies
    ADD CONSTRAINT fk_patient_allergies_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_patient_allergies_tenant_id ON core.patient_allergies (tenant_id);
CREATE INDEX idx_patient_allergies_tenant_active ON core.patient_allergies (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.patient_contacts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    patient_id          UUID NOT NULL,
    name                VARCHAR(200) NOT NULL,
    relationship        VARCHAR(50) NOT NULL,
    phone               VARCHAR(20) NOT NULL,
    email               VARCHAR(255),
    is_emergency        BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.patient_contacts IS 'Emergency and guardian contacts for patients.';
CREATE UNIQUE INDEX uq_patient_contacts_tenant_id_id ON core.patient_contacts (tenant_id, id);
ALTER TABLE core.patient_contacts
    ADD CONSTRAINT fk_patient_contacts_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_patient_contacts_tenant_id ON core.patient_contacts (tenant_id);
CREATE INDEX idx_patient_contacts_tenant_active ON core.patient_contacts (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.patient_documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    patient_id          UUID NOT NULL,
    document_type       VARCHAR(50) NOT NULL CHECK (document_type IN ('id_proof', 'consent', 'report', 'other')),
    file_name           VARCHAR(255) NOT NULL,
    file_path           TEXT NOT NULL,
    file_size_bytes     BIGINT NOT NULL CHECK (file_size_bytes >= 0),
    mime_type           VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.patient_documents IS 'Attached patient documents and consents.';
CREATE UNIQUE INDEX uq_patient_documents_tenant_id_id ON core.patient_documents (tenant_id, id);
ALTER TABLE core.patient_documents
    ADD CONSTRAINT fk_patient_documents_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_patient_documents_tenant_id ON core.patient_documents (tenant_id);
CREATE INDEX idx_patient_documents_tenant_active ON core.patient_documents (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.doctors (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    staff_id            UUID NOT NULL,
    registration_number VARCHAR(50),
    specialization      VARCHAR(150) NOT NULL,
    qualification       VARCHAR(255),
    consultation_fee    DECIMAL(10,2) NOT NULL CHECK (consultation_fee >= 0),
    follow_up_fee       DECIMAL(10,2) CHECK (follow_up_fee IS NULL OR follow_up_fee >= 0),
    department_id       UUID,
    bio                 TEXT,
    is_available        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.doctors IS 'Doctor profiles extending staff records.';
CREATE UNIQUE INDEX uq_doctors_tenant_id_id ON core.doctors (tenant_id, id);
ALTER TABLE core.doctors
    ADD CONSTRAINT fk_doctors_staff FOREIGN KEY (tenant_id, staff_id)
    REFERENCES core.staff (tenant_id, id);
ALTER TABLE core.doctors
    ADD CONSTRAINT fk_doctors_department FOREIGN KEY (tenant_id, department_id)
    REFERENCES core.departments (tenant_id, id);
CREATE UNIQUE INDEX uq_doctors_tenant_staff ON core.doctors (tenant_id, staff_id);
CREATE INDEX idx_doctors_tenant_id ON core.doctors (tenant_id);
CREATE INDEX idx_doctors_tenant_active ON core.doctors (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE core.doctor_schedules (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    doctor_id           UUID NOT NULL,
    day_of_week         SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time          TIME NOT NULL,
    end_time            TIME NOT NULL,
    slot_duration_minutes INTEGER NOT NULL CHECK (slot_duration_minutes > 0),
    max_patients_per_slot INTEGER NOT NULL DEFAULT 1 CHECK (max_patients_per_slot > 0),
    location_id         UUID,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (end_time > start_time),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE core.doctor_schedules IS 'Doctor availability schedules and appointment slots.';
CREATE UNIQUE INDEX uq_doctor_schedules_tenant_id_id ON core.doctor_schedules (tenant_id, id);
ALTER TABLE core.doctor_schedules
    ADD CONSTRAINT fk_doctor_schedules_doctor FOREIGN KEY (tenant_id, doctor_id)
    REFERENCES core.doctors (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE core.doctor_schedules
    ADD CONSTRAINT fk_doctor_schedules_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE INDEX idx_doctor_schedules_tenant_id ON core.doctor_schedules (tenant_id);
CREATE INDEX idx_doctor_schedules_tenant_active ON core.doctor_schedules (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- CLINICAL SCHEMA — Appointments & OPD
-- =============================================================================
CREATE TABLE clinical.appointments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    patient_id          UUID NOT NULL,
    doctor_id           UUID NOT NULL,
    location_id         UUID,
    appointment_date    DATE NOT NULL,
    start_time          TIME NOT NULL,
    end_time            TIME NOT NULL,
    appointment_type    VARCHAR(20) NOT NULL CHECK (appointment_type IN ('new', 'follow_up', 'emergency')),
    status              VARCHAR(20) NOT NULL DEFAULT 'scheduled'
                        CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
    notes               TEXT,
    cancelled_reason    TEXT,
    reminder_sent_at    TIMESTAMPTZ,
    CHECK (end_time > start_time),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.appointments IS 'Scheduled patient appointments.';
CREATE UNIQUE INDEX uq_appointments_tenant_id_id ON clinical.appointments (tenant_id, id);
ALTER TABLE clinical.appointments
    ADD CONSTRAINT fk_appointments_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE clinical.appointments
    ADD CONSTRAINT fk_appointments_doctor FOREIGN KEY (tenant_id, doctor_id)
    REFERENCES core.doctors (tenant_id, id);
ALTER TABLE clinical.appointments
    ADD CONSTRAINT fk_appointments_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE INDEX idx_appointments_doctor_date ON clinical.appointments (tenant_id, doctor_id, appointment_date);
CREATE INDEX idx_appointments_patient ON clinical.appointments (tenant_id, patient_id);
CREATE INDEX idx_appointments_status_date ON clinical.appointments (tenant_id, status, appointment_date);
CREATE INDEX idx_appointments_tenant_id ON clinical.appointments (tenant_id);
CREATE INDEX idx_appointments_tenant_active ON clinical.appointments (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_visits (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    visit_number        VARCHAR(20) NOT NULL,
    patient_id          UUID NOT NULL,
    doctor_id           UUID NOT NULL,
    appointment_id      UUID,
    location_id         UUID,
    visit_date          DATE NOT NULL,
    visit_type          VARCHAR(20) NOT NULL CHECK (visit_type IN ('walk_in', 'appointment')),
    status              VARCHAR(20) NOT NULL DEFAULT 'waiting'
                        CHECK (status IN ('waiting', 'in_consultation', 'completed', 'cancelled')),
    token_number        INTEGER,
    chief_complaint     TEXT,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_visits IS 'Outpatient department encounters.';
CREATE UNIQUE INDEX uq_opd_visits_tenant_id_id ON clinical.opd_visits (tenant_id, id);
ALTER TABLE clinical.opd_visits
    ADD CONSTRAINT fk_opd_visits_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE clinical.opd_visits
    ADD CONSTRAINT fk_opd_visits_doctor FOREIGN KEY (tenant_id, doctor_id)
    REFERENCES core.doctors (tenant_id, id);
ALTER TABLE clinical.opd_visits
    ADD CONSTRAINT fk_opd_visits_appointment FOREIGN KEY (tenant_id, appointment_id)
    REFERENCES clinical.appointments (tenant_id, id) ON DELETE SET NULL;
ALTER TABLE clinical.opd_visits
    ADD CONSTRAINT fk_opd_visits_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_opd_visits_tenant_number ON clinical.opd_visits (tenant_id, visit_number);
CREATE INDEX idx_opd_visits_doctor_date ON clinical.opd_visits (tenant_id, doctor_id, visit_date);
CREATE INDEX idx_opd_visits_patient ON clinical.opd_visits (tenant_id, patient_id);
CREATE INDEX idx_opd_visits_tenant_id ON clinical.opd_visits (tenant_id);
CREATE INDEX idx_opd_visits_tenant_active ON clinical.opd_visits (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_queue (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    opd_visit_id        UUID NOT NULL,
    doctor_id           UUID NOT NULL,
    token_number        INTEGER NOT NULL,
    queue_date          DATE NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'waiting'
                        CHECK (status IN ('waiting', 'called', 'in_consultation', 'completed', 'skipped')),
    priority            VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (priority IN ('normal', 'urgent')),
    called_at           TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_queue IS 'OPD token queue per doctor.';
CREATE UNIQUE INDEX uq_opd_queue_tenant_id_id ON clinical.opd_queue (tenant_id, id);
ALTER TABLE clinical.opd_queue
    ADD CONSTRAINT fk_opd_queue_visit FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE clinical.opd_queue
    ADD CONSTRAINT fk_opd_queue_doctor FOREIGN KEY (tenant_id, doctor_id)
    REFERENCES core.doctors (tenant_id, id);
CREATE INDEX idx_opd_queue_doctor_date ON clinical.opd_queue (tenant_id, doctor_id, queue_date, status);
CREATE INDEX idx_opd_queue_tenant_id ON clinical.opd_queue (tenant_id);
CREATE INDEX idx_opd_queue_tenant_active ON clinical.opd_queue (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_vitals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    opd_visit_id        UUID NOT NULL,
    recorded_at         TIMESTAMPTZ NOT NULL,
    blood_pressure_systolic  SMALLINT,
    blood_pressure_diastolic SMALLINT,
    pulse_rate          SMALLINT,
    temperature         DECIMAL(4,1),
    respiratory_rate    SMALLINT,
    spo2                SMALLINT,
    weight_kg           DECIMAL(5,2),
    height_cm           DECIMAL(5,1),
    bmi                 DECIMAL(4,1),
    notes               TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_vitals IS 'Vital signs recorded during OPD visits.';
CREATE UNIQUE INDEX uq_opd_vitals_tenant_id_id ON clinical.opd_vitals (tenant_id, id);
ALTER TABLE clinical.opd_vitals
    ADD CONSTRAINT fk_opd_vitals_visit FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_opd_vitals_tenant_id ON clinical.opd_vitals (tenant_id);
CREATE INDEX idx_opd_vitals_tenant_active ON clinical.opd_vitals (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_clinical_notes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    opd_visit_id        UUID NOT NULL,
    note_type           VARCHAR(30) NOT NULL CHECK (note_type IN ('examination', 'diagnosis', 'plan', 'general')),
    content             TEXT NOT NULL,
    icd_code            VARCHAR(10),
    icd_description     VARCHAR(255),
    is_final            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_clinical_notes IS 'Consultation notes and diagnosis for OPD visits.';
CREATE UNIQUE INDEX uq_opd_clinical_notes_tenant_id_id ON clinical.opd_clinical_notes (tenant_id, id);
ALTER TABLE clinical.opd_clinical_notes
    ADD CONSTRAINT fk_opd_clinical_notes_visit FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_opd_clinical_notes_tenant_id ON clinical.opd_clinical_notes (tenant_id);
CREATE INDEX idx_opd_clinical_notes_tenant_active ON clinical.opd_clinical_notes (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE pharmacy.medicines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    code                VARCHAR(20) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    generic_name        VARCHAR(255),
    category            VARCHAR(50) NOT NULL,
    unit                VARCHAR(20) NOT NULL,
    strength            VARCHAR(50),
    manufacturer        VARCHAR(255),
    unit_price          DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    reorder_level       INTEGER NOT NULL DEFAULT 0 CHECK (reorder_level >= 0),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE pharmacy.medicines IS 'Drug and medicine master catalog.';
CREATE UNIQUE INDEX uq_medicines_tenant_id_id ON pharmacy.medicines (tenant_id, id);
CREATE UNIQUE INDEX uq_medicines_tenant_code ON pharmacy.medicines (tenant_id, code);
CREATE INDEX idx_medicines_tenant_id ON pharmacy.medicines (tenant_id);
CREATE INDEX idx_medicines_tenant_active ON pharmacy.medicines (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_prescriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    opd_visit_id        UUID NOT NULL,
    patient_id          UUID NOT NULL,
    doctor_id           UUID NOT NULL,
    prescription_number VARCHAR(20) NOT NULL,
    prescribed_at       TIMESTAMPTZ NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'dispensed', 'partially_dispensed', 'cancelled')),
    notes               TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_prescriptions IS 'OPD prescription headers.';
CREATE UNIQUE INDEX uq_opd_prescriptions_tenant_id_id ON clinical.opd_prescriptions (tenant_id, id);
ALTER TABLE clinical.opd_prescriptions
    ADD CONSTRAINT fk_opd_rx_visit FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id);
ALTER TABLE clinical.opd_prescriptions
    ADD CONSTRAINT fk_opd_rx_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE clinical.opd_prescriptions
    ADD CONSTRAINT fk_opd_rx_doctor FOREIGN KEY (tenant_id, doctor_id)
    REFERENCES core.doctors (tenant_id, id);
CREATE UNIQUE INDEX uq_opd_prescriptions_number ON clinical.opd_prescriptions (tenant_id, prescription_number);
CREATE INDEX idx_opd_prescriptions_tenant_id ON clinical.opd_prescriptions (tenant_id);
CREATE INDEX idx_opd_prescriptions_tenant_active ON clinical.opd_prescriptions (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_prescription_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    prescription_id     UUID NOT NULL,
    medicine_id         UUID,
    medicine_name       VARCHAR(255) NOT NULL,
    dosage              VARCHAR(100) NOT NULL,
    frequency           VARCHAR(100) NOT NULL,
    duration            VARCHAR(100) NOT NULL,
    route               VARCHAR(50),
    instructions        TEXT,
    quantity            INTEGER CHECK (quantity IS NULL OR quantity > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_prescription_items IS 'Line items on OPD prescriptions.';
CREATE UNIQUE INDEX uq_opd_prescription_items_tenant_id_id ON clinical.opd_prescription_items (tenant_id, id);
ALTER TABLE clinical.opd_prescription_items
    ADD CONSTRAINT fk_opd_rx_items_rx FOREIGN KEY (tenant_id, prescription_id)
    REFERENCES clinical.opd_prescriptions (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE clinical.opd_prescription_items
    ADD CONSTRAINT fk_opd_rx_items_medicine FOREIGN KEY (tenant_id, medicine_id)
    REFERENCES pharmacy.medicines (tenant_id, id);
CREATE INDEX idx_opd_prescription_items_tenant_id ON clinical.opd_prescription_items (tenant_id);
CREATE INDEX idx_opd_prescription_items_tenant_active ON clinical.opd_prescription_items (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.opd_referrals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    opd_visit_id        UUID NOT NULL,
    patient_id          UUID NOT NULL,
    referring_doctor_id UUID NOT NULL,
    referred_doctor_id  UUID,
    referral_type       VARCHAR(20) NOT NULL CHECK (referral_type IN ('internal', 'external')),
    external_facility   VARCHAR(255),
    reason              TEXT NOT NULL,
    urgency             VARCHAR(10) NOT NULL DEFAULT 'routine' CHECK (urgency IN ('routine', 'urgent', 'emergency')),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'accepted', 'completed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.opd_referrals IS 'Internal and external referrals from OPD visits.';
CREATE UNIQUE INDEX uq_opd_referrals_tenant_id_id ON clinical.opd_referrals (tenant_id, id);
ALTER TABLE clinical.opd_referrals
    ADD CONSTRAINT fk_opd_referrals_visit FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id);
ALTER TABLE clinical.opd_referrals
    ADD CONSTRAINT fk_opd_referrals_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE clinical.opd_referrals
    ADD CONSTRAINT fk_opd_referrals_referring FOREIGN KEY (tenant_id, referring_doctor_id)
    REFERENCES core.doctors (tenant_id, id);
ALTER TABLE clinical.opd_referrals
    ADD CONSTRAINT fk_opd_referrals_referred FOREIGN KEY (tenant_id, referred_doctor_id)
    REFERENCES core.doctors (tenant_id, id);
CREATE INDEX idx_opd_referrals_tenant_id ON clinical.opd_referrals (tenant_id);
CREATE INDEX idx_opd_referrals_tenant_active ON clinical.opd_referrals (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- CLINICAL SCHEMA — IPD & Bed Management
-- =============================================================================
CREATE TABLE clinical.wards (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    name                VARCHAR(150) NOT NULL,
    code                VARCHAR(20) NOT NULL,
    ward_type           VARCHAR(30) NOT NULL,
    floor               VARCHAR(10),
    location_id         UUID,
    capacity            INTEGER NOT NULL CHECK (capacity >= 0),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.wards IS 'Hospital wards for inpatient care.';
CREATE UNIQUE INDEX uq_wards_tenant_id_id ON clinical.wards (tenant_id, id);
ALTER TABLE clinical.wards
    ADD CONSTRAINT fk_wards_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_wards_tenant_code ON clinical.wards (tenant_id, code);
CREATE INDEX idx_wards_tenant_id ON clinical.wards (tenant_id);
CREATE INDEX idx_wards_tenant_active ON clinical.wards (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.rooms (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    ward_id             UUID NOT NULL,
    room_number         VARCHAR(20) NOT NULL,
    room_type           VARCHAR(30) NOT NULL CHECK (room_type IN ('private', 'semi_private', 'general')),
    daily_charge        DECIMAL(10,2) CHECK (daily_charge IS NULL OR daily_charge >= 0),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.rooms IS 'Rooms within hospital wards.';
CREATE UNIQUE INDEX uq_rooms_tenant_id_id ON clinical.rooms (tenant_id, id);
ALTER TABLE clinical.rooms
    ADD CONSTRAINT fk_rooms_ward FOREIGN KEY (tenant_id, ward_id)
    REFERENCES clinical.wards (tenant_id, id);
CREATE UNIQUE INDEX uq_rooms_ward_number ON clinical.rooms (tenant_id, ward_id, room_number);
CREATE INDEX idx_rooms_tenant_id ON clinical.rooms (tenant_id);
CREATE INDEX idx_rooms_tenant_active ON clinical.rooms (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.beds (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    room_id             UUID NOT NULL,
    bed_number          VARCHAR(10) NOT NULL,
    bed_type            VARCHAR(30) NOT NULL CHECK (bed_type IN ('standard', 'icu', 'ventilator')),
    status              VARCHAR(20) NOT NULL DEFAULT 'available'
                        CHECK (status IN ('available', 'occupied', 'maintenance', 'reserved')),
    daily_charge        DECIMAL(10,2) CHECK (daily_charge IS NULL OR daily_charge >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.beds IS 'Beds within rooms for patient occupancy.';
CREATE UNIQUE INDEX uq_beds_tenant_id_id ON clinical.beds (tenant_id, id);
ALTER TABLE clinical.beds
    ADD CONSTRAINT fk_beds_room FOREIGN KEY (tenant_id, room_id)
    REFERENCES clinical.rooms (tenant_id, id);
CREATE UNIQUE INDEX uq_beds_room_number ON clinical.beds (tenant_id, room_id, bed_number);
CREATE INDEX idx_beds_tenant_status ON clinical.beds (tenant_id, status);
CREATE INDEX idx_beds_tenant_id ON clinical.beds (tenant_id);
CREATE INDEX idx_beds_tenant_active ON clinical.beds (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.admissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    admission_number    VARCHAR(20) NOT NULL,
    patient_id          UUID NOT NULL,
    admitting_doctor_id UUID NOT NULL,
    attending_doctor_id UUID,
    bed_id              UUID NOT NULL,
    location_id         UUID,
    admission_date      TIMESTAMPTZ NOT NULL,
    expected_discharge_date DATE,
    actual_discharge_date TIMESTAMPTZ,
    admission_type      VARCHAR(20) NOT NULL CHECK (admission_type IN ('emergency', 'planned', 'transfer')),
    status              VARCHAR(20) NOT NULL DEFAULT 'admitted'
                        CHECK (status IN ('admitted', 'under_treatment', 'discharged', 'transferred', 'deceased')),
    diagnosis_on_admission TEXT,
    admission_notes     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.admissions IS 'Inpatient admission records.';
CREATE UNIQUE INDEX uq_admissions_tenant_id_id ON clinical.admissions (tenant_id, id);
ALTER TABLE clinical.admissions
    ADD CONSTRAINT fk_admissions_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE clinical.admissions
    ADD CONSTRAINT fk_admissions_admitting_doc FOREIGN KEY (tenant_id, admitting_doctor_id)
    REFERENCES core.doctors (tenant_id, id);
ALTER TABLE clinical.admissions
    ADD CONSTRAINT fk_admissions_attending_doc FOREIGN KEY (tenant_id, attending_doctor_id)
    REFERENCES core.doctors (tenant_id, id);
ALTER TABLE clinical.admissions
    ADD CONSTRAINT fk_admissions_bed FOREIGN KEY (tenant_id, bed_id)
    REFERENCES clinical.beds (tenant_id, id);
ALTER TABLE clinical.admissions
    ADD CONSTRAINT fk_admissions_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_admissions_tenant_number ON clinical.admissions (tenant_id, admission_number);
CREATE INDEX idx_admissions_patient ON clinical.admissions (tenant_id, patient_id);
CREATE INDEX idx_admissions_bed_status ON clinical.admissions (tenant_id, bed_id, status);
CREATE INDEX idx_admissions_status_date ON clinical.admissions (tenant_id, status, admission_date);
CREATE INDEX idx_admissions_tenant_id ON clinical.admissions (tenant_id);
CREATE INDEX idx_admissions_tenant_active ON clinical.admissions (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.admission_transfers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    admission_id        UUID NOT NULL,
    from_bed_id         UUID NOT NULL,
    to_bed_id           UUID NOT NULL,
    transfer_reason     TEXT,
    transferred_at      TIMESTAMPTZ NOT NULL,
    transferred_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.admission_transfers IS 'Ward and bed transfer history for admissions.';
CREATE UNIQUE INDEX uq_admission_transfers_tenant_id_id ON clinical.admission_transfers (tenant_id, id);
ALTER TABLE clinical.admission_transfers
    ADD CONSTRAINT fk_adm_transfers_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE clinical.admission_transfers
    ADD CONSTRAINT fk_adm_transfers_from_bed FOREIGN KEY (tenant_id, from_bed_id)
    REFERENCES clinical.beds (tenant_id, id);
ALTER TABLE clinical.admission_transfers
    ADD CONSTRAINT fk_adm_transfers_to_bed FOREIGN KEY (tenant_id, to_bed_id)
    REFERENCES clinical.beds (tenant_id, id);
ALTER TABLE clinical.admission_transfers
    ADD CONSTRAINT fk_adm_transfers_user FOREIGN KEY (tenant_id, transferred_by)
    REFERENCES core.users (tenant_id, id);
CREATE INDEX idx_admission_transfers_tenant_id ON clinical.admission_transfers (tenant_id);
CREATE INDEX idx_admission_transfers_tenant_active ON clinical.admission_transfers (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.nursing_notes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    admission_id        UUID NOT NULL,
    nurse_id            UUID,
    note_type           VARCHAR(30) NOT NULL CHECK (note_type IN ('assessment', 'care_plan', 'progress', 'incident')),
    content             TEXT NOT NULL,
    recorded_at         TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.nursing_notes IS 'Nursing documentation for inpatient admissions.';
CREATE UNIQUE INDEX uq_nursing_notes_tenant_id_id ON clinical.nursing_notes (tenant_id, id);
ALTER TABLE clinical.nursing_notes
    ADD CONSTRAINT fk_nursing_notes_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE clinical.nursing_notes
    ADD CONSTRAINT fk_nursing_notes_nurse FOREIGN KEY (tenant_id, nurse_id)
    REFERENCES core.staff (tenant_id, id);
CREATE INDEX idx_nursing_notes_tenant_id ON clinical.nursing_notes (tenant_id);
CREATE INDEX idx_nursing_notes_tenant_active ON clinical.nursing_notes (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.ipd_vitals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    admission_id        UUID NOT NULL,
    recorded_at         TIMESTAMPTZ NOT NULL,
    blood_pressure_systolic  SMALLINT,
    blood_pressure_diastolic SMALLINT,
    pulse_rate          SMALLINT,
    temperature         DECIMAL(4,1),
    respiratory_rate    SMALLINT,
    spo2                SMALLINT,
    notes               TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.ipd_vitals IS 'Inpatient vital signs charting.';
CREATE UNIQUE INDEX uq_ipd_vitals_tenant_id_id ON clinical.ipd_vitals (tenant_id, id);
ALTER TABLE clinical.ipd_vitals
    ADD CONSTRAINT fk_ipd_vitals_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_ipd_vitals_tenant_id ON clinical.ipd_vitals (tenant_id);
CREATE INDEX idx_ipd_vitals_tenant_active ON clinical.ipd_vitals (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.discharge_summaries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    admission_id        UUID NOT NULL,
    patient_id          UUID NOT NULL,
    discharging_doctor_id UUID NOT NULL,
    diagnosis           TEXT NOT NULL,
    treatment_summary   TEXT NOT NULL,
    medications_on_discharge TEXT,
    follow_up_instructions TEXT,
    follow_up_date      DATE,
    discharged_at       TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.discharge_summaries IS 'Discharge documentation for inpatient stays.';
CREATE UNIQUE INDEX uq_discharge_summaries_tenant_id_id ON clinical.discharge_summaries (tenant_id, id);
ALTER TABLE clinical.discharge_summaries
    ADD CONSTRAINT fk_discharge_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id);
ALTER TABLE clinical.discharge_summaries
    ADD CONSTRAINT fk_discharge_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE clinical.discharge_summaries
    ADD CONSTRAINT fk_discharge_doctor FOREIGN KEY (tenant_id, discharging_doctor_id)
    REFERENCES core.doctors (tenant_id, id);
CREATE INDEX idx_discharge_summaries_tenant_id ON clinical.discharge_summaries (tenant_id);
CREATE INDEX idx_discharge_summaries_tenant_active ON clinical.discharge_summaries (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- BILLING SCHEMA
-- =============================================================================
CREATE TABLE billing.billing_services (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    code                VARCHAR(20) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    category            VARCHAR(50) NOT NULL
                        CHECK (category IN ('consultation', 'procedure', 'lab', 'pharmacy', 'room', 'nursing', 'other')),
    department_id       UUID,
    price               DECIMAL(12,2) NOT NULL CHECK (price >= 0),
    tax_rate            DECIMAL(5,2) NOT NULL DEFAULT 0 CHECK (tax_rate >= 0),
    is_tax_inclusive    BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE billing.billing_services IS 'Service and charge master for billing.';
CREATE UNIQUE INDEX uq_billing_services_tenant_id_id ON billing.billing_services (tenant_id, id);
ALTER TABLE billing.billing_services
    ADD CONSTRAINT fk_billing_services_dept FOREIGN KEY (tenant_id, department_id)
    REFERENCES core.departments (tenant_id, id);
CREATE UNIQUE INDEX uq_billing_services_tenant_code ON billing.billing_services (tenant_id, code);
CREATE INDEX idx_billing_services_tenant_id ON billing.billing_services (tenant_id);
CREATE INDEX idx_billing_services_tenant_active ON billing.billing_services (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE billing.invoices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    invoice_number      VARCHAR(20) NOT NULL,
    patient_id          UUID NOT NULL,
    opd_visit_id        UUID,
    admission_id        UUID,
    location_id         UUID,
    invoice_date        DATE NOT NULL,
    due_date            DATE,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'finalized', 'partially_paid', 'paid', 'voided')),
    subtotal            DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_amount          DECIMAL(12,2) NOT NULL DEFAULT 0,
    discount_amount     DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_amount        DECIMAL(12,2) NOT NULL DEFAULT 0,
    paid_amount         DECIMAL(12,2) NOT NULL DEFAULT 0,
    balance_amount      DECIMAL(12,2) NOT NULL DEFAULT 0,
    notes               TEXT,
    finalized_at        TIMESTAMPTZ,
    voided_at           TIMESTAMPTZ,
    void_reason         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE billing.invoices IS 'Invoice headers for patient billing.';
CREATE UNIQUE INDEX uq_invoices_tenant_id_id ON billing.invoices (tenant_id, id);
ALTER TABLE billing.invoices
    ADD CONSTRAINT fk_invoices_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE billing.invoices
    ADD CONSTRAINT fk_invoices_opd_visit FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id);
ALTER TABLE billing.invoices
    ADD CONSTRAINT fk_invoices_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id);
ALTER TABLE billing.invoices
    ADD CONSTRAINT fk_invoices_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_invoices_tenant_number ON billing.invoices (tenant_id, invoice_number);
CREATE INDEX idx_invoices_patient ON billing.invoices (tenant_id, patient_id);
CREATE INDEX idx_invoices_status_date ON billing.invoices (tenant_id, status, invoice_date);
CREATE INDEX idx_invoices_tenant_id ON billing.invoices (tenant_id);
CREATE INDEX idx_invoices_tenant_active ON billing.invoices (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE clinical.ipd_daily_charges (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    admission_id        UUID NOT NULL,
    billing_service_id  UUID,
    charge_date         DATE NOT NULL,
    description         VARCHAR(255) NOT NULL,
    amount              DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    is_billed           BOOLEAN NOT NULL DEFAULT FALSE,
    invoice_id          UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE clinical.ipd_daily_charges IS 'Daily IPD charge accruals linked to admissions.';
CREATE UNIQUE INDEX uq_ipd_daily_charges_tenant_id_id ON clinical.ipd_daily_charges (tenant_id, id);
ALTER TABLE clinical.ipd_daily_charges
    ADD CONSTRAINT fk_ipd_charges_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE clinical.ipd_daily_charges
    ADD CONSTRAINT fk_ipd_charges_service FOREIGN KEY (tenant_id, billing_service_id)
    REFERENCES billing.billing_services (tenant_id, id);
ALTER TABLE clinical.ipd_daily_charges
    ADD CONSTRAINT fk_ipd_charges_invoice FOREIGN KEY (tenant_id, invoice_id)
    REFERENCES billing.invoices (tenant_id, id);
CREATE INDEX idx_ipd_daily_charges_tenant_id ON clinical.ipd_daily_charges (tenant_id);
CREATE INDEX idx_ipd_daily_charges_tenant_active ON clinical.ipd_daily_charges (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE billing.invoice_line_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    invoice_id          UUID NOT NULL,
    billing_service_id  UUID,
    description         VARCHAR(255) NOT NULL,
    quantity            DECIMAL(10,2) NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price          DECIMAL(12,2) NOT NULL,
    tax_rate            DECIMAL(5,2) NOT NULL DEFAULT 0,
    tax_amount          DECIMAL(12,2) NOT NULL DEFAULT 0,
    discount_amount     DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_amount        DECIMAL(12,2) NOT NULL,
    source_type         VARCHAR(30) CHECK (source_type IN ('opd', 'ipd', 'lab', 'pharmacy', 'manual')),
    source_id           UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE billing.invoice_line_items IS 'Line items on patient invoices.';
CREATE UNIQUE INDEX uq_invoice_line_items_tenant_id_id ON billing.invoice_line_items (tenant_id, id);
ALTER TABLE billing.invoice_line_items
    ADD CONSTRAINT fk_invoice_line_items_invoice FOREIGN KEY (tenant_id, invoice_id)
    REFERENCES billing.invoices (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE billing.invoice_line_items
    ADD CONSTRAINT fk_invoice_line_items_service FOREIGN KEY (tenant_id, billing_service_id)
    REFERENCES billing.billing_services (tenant_id, id) ON DELETE SET NULL;
CREATE INDEX idx_invoice_line_items_tenant_id ON billing.invoice_line_items (tenant_id);
CREATE INDEX idx_invoice_line_items_tenant_active ON billing.invoice_line_items (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE billing.payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    receipt_number      VARCHAR(20) NOT NULL,
    patient_id          UUID NOT NULL,
    payment_date        TIMESTAMPTZ NOT NULL,
    amount              DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    payment_mode        VARCHAR(20) NOT NULL
                        CHECK (payment_mode IN ('cash', 'card', 'upi', 'bank_transfer', 'insurance')),
    reference_number    VARCHAR(100),
    status              VARCHAR(20) NOT NULL DEFAULT 'completed'
                        CHECK (status IN ('completed', 'pending', 'failed', 'refunded')),
    notes               TEXT,
    collected_by        UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE billing.payments IS 'Payment transactions from patients.';
CREATE UNIQUE INDEX uq_payments_tenant_id_id ON billing.payments (tenant_id, id);
ALTER TABLE billing.payments
    ADD CONSTRAINT fk_payments_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE billing.payments
    ADD CONSTRAINT fk_payments_collected_by FOREIGN KEY (tenant_id, collected_by)
    REFERENCES core.users (tenant_id, id);
CREATE UNIQUE INDEX uq_payments_tenant_receipt ON billing.payments (tenant_id, receipt_number);
CREATE INDEX idx_payments_patient_date ON billing.payments (tenant_id, patient_id, payment_date);
CREATE INDEX idx_payments_tenant_id ON billing.payments (tenant_id);
CREATE INDEX idx_payments_tenant_active ON billing.payments (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE billing.payment_allocations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    payment_id          UUID NOT NULL,
    invoice_id          UUID NOT NULL,
    allocated_amount    DECIMAL(12,2) NOT NULL CHECK (allocated_amount > 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE billing.payment_allocations IS 'Allocation of payments across invoices.';
CREATE UNIQUE INDEX uq_payment_allocations_tenant_id_id ON billing.payment_allocations (tenant_id, id);
ALTER TABLE billing.payment_allocations
    ADD CONSTRAINT fk_payment_alloc_payment FOREIGN KEY (tenant_id, payment_id)
    REFERENCES billing.payments (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE billing.payment_allocations
    ADD CONSTRAINT fk_payment_alloc_invoice FOREIGN KEY (tenant_id, invoice_id)
    REFERENCES billing.invoices (tenant_id, id);
CREATE INDEX idx_payment_allocations_tenant_id ON billing.payment_allocations (tenant_id);
CREATE INDEX idx_payment_allocations_tenant_active ON billing.payment_allocations (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE billing.invoice_adjustments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    invoice_id          UUID NOT NULL,
    adjustment_type     VARCHAR(20) NOT NULL
                        CHECK (adjustment_type IN ('discount', 'void', 'write_off', 'correction')),
    amount              DECIMAL(12,2) NOT NULL,
    reason              TEXT NOT NULL,
    approved_by         UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE billing.invoice_adjustments IS 'Discounts, voids, write-offs, and corrections on invoices.';
CREATE UNIQUE INDEX uq_invoice_adjustments_tenant_id_id ON billing.invoice_adjustments (tenant_id, id);
ALTER TABLE billing.invoice_adjustments
    ADD CONSTRAINT fk_invoice_adj_invoice FOREIGN KEY (tenant_id, invoice_id)
    REFERENCES billing.invoices (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE billing.invoice_adjustments
    ADD CONSTRAINT fk_invoice_adj_approved_by FOREIGN KEY (tenant_id, approved_by)
    REFERENCES core.users (tenant_id, id);
CREATE INDEX idx_invoice_adjustments_tenant_id ON billing.invoice_adjustments (tenant_id);
CREATE INDEX idx_invoice_adjustments_tenant_active ON billing.invoice_adjustments (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- PHARMACY SCHEMA
-- =============================================================================
CREATE TABLE pharmacy.pharmacy_inventory (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    medicine_id         UUID NOT NULL,
    batch_number        VARCHAR(50) NOT NULL,
    quantity_on_hand    INTEGER NOT NULL DEFAULT 0 CHECK (quantity_on_hand >= 0),
    unit_cost           DECIMAL(10,2) NOT NULL CHECK (unit_cost >= 0),
    expiry_date         DATE NOT NULL,
    location_id         UUID,
    supplier_name       VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE pharmacy.pharmacy_inventory IS 'Pharmacy stock by medicine and batch.';
CREATE UNIQUE INDEX uq_pharmacy_inventory_tenant_id_id ON pharmacy.pharmacy_inventory (tenant_id, id);
ALTER TABLE pharmacy.pharmacy_inventory
    ADD CONSTRAINT fk_pharmacy_inv_medicine FOREIGN KEY (tenant_id, medicine_id)
    REFERENCES pharmacy.medicines (tenant_id, id);
ALTER TABLE pharmacy.pharmacy_inventory
    ADD CONSTRAINT fk_pharmacy_inv_location FOREIGN KEY (tenant_id, location_id)
    REFERENCES platform.tenant_locations (tenant_id, id);
CREATE UNIQUE INDEX uq_pharmacy_inventory_batch ON pharmacy.pharmacy_inventory (tenant_id, medicine_id, batch_number);
CREATE INDEX idx_pharmacy_inventory_med_expiry ON pharmacy.pharmacy_inventory (tenant_id, medicine_id, expiry_date);
CREATE INDEX idx_pharmacy_inventory_tenant_id ON pharmacy.pharmacy_inventory (tenant_id);
CREATE INDEX idx_pharmacy_inventory_tenant_active ON pharmacy.pharmacy_inventory (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE pharmacy.purchase_orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    po_number           VARCHAR(20) NOT NULL,
    supplier_name       VARCHAR(255) NOT NULL,
    order_date          DATE NOT NULL,
    expected_delivery_date DATE,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'ordered', 'received', 'cancelled')),
    total_amount        DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    notes               TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE pharmacy.purchase_orders IS 'Stock purchase orders for pharmacy replenishment.';
CREATE UNIQUE INDEX uq_purchase_orders_tenant_id_id ON pharmacy.purchase_orders (tenant_id, id);
CREATE UNIQUE INDEX uq_purchase_orders_tenant_number ON pharmacy.purchase_orders (tenant_id, po_number);
CREATE INDEX idx_purchase_orders_tenant_id ON pharmacy.purchase_orders (tenant_id);
CREATE INDEX idx_purchase_orders_tenant_active ON pharmacy.purchase_orders (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE pharmacy.dispense_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    dispense_number     VARCHAR(20) NOT NULL,
    prescription_id     UUID,
    patient_id          UUID NOT NULL,
    dispensed_by        UUID,
    dispensed_at        TIMESTAMPTZ NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'completed'
                        CHECK (status IN ('completed', 'partial', 'cancelled')),
    total_amount        DECIMAL(12,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE pharmacy.dispense_records IS 'Pharmacy dispensing events.';
CREATE UNIQUE INDEX uq_dispense_records_tenant_id_id ON pharmacy.dispense_records (tenant_id, id);
ALTER TABLE pharmacy.dispense_records
    ADD CONSTRAINT fk_dispense_rx FOREIGN KEY (tenant_id, prescription_id)
    REFERENCES clinical.opd_prescriptions (tenant_id, id);
ALTER TABLE pharmacy.dispense_records
    ADD CONSTRAINT fk_dispense_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE pharmacy.dispense_records
    ADD CONSTRAINT fk_dispense_by FOREIGN KEY (tenant_id, dispensed_by)
    REFERENCES core.users (tenant_id, id);
CREATE UNIQUE INDEX uq_dispense_records_number ON pharmacy.dispense_records (tenant_id, dispense_number);
CREATE INDEX idx_dispense_records_tenant_id ON pharmacy.dispense_records (tenant_id);
CREATE INDEX idx_dispense_records_tenant_active ON pharmacy.dispense_records (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE pharmacy.dispense_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    dispense_id         UUID NOT NULL,
    medicine_id         UUID NOT NULL,
    inventory_id        UUID,
    prescription_item_id UUID,
    quantity_dispensed  INTEGER NOT NULL CHECK (quantity_dispensed > 0),
    unit_price          DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    total_price         DECIMAL(12,2) NOT NULL CHECK (total_price >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE pharmacy.dispense_items IS 'Line items dispensed in pharmacy events.';
CREATE UNIQUE INDEX uq_dispense_items_tenant_id_id ON pharmacy.dispense_items (tenant_id, id);
ALTER TABLE pharmacy.dispense_items
    ADD CONSTRAINT fk_dispense_items_record FOREIGN KEY (tenant_id, dispense_id)
    REFERENCES pharmacy.dispense_records (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE pharmacy.dispense_items
    ADD CONSTRAINT fk_dispense_items_medicine FOREIGN KEY (tenant_id, medicine_id)
    REFERENCES pharmacy.medicines (tenant_id, id);
ALTER TABLE pharmacy.dispense_items
    ADD CONSTRAINT fk_dispense_items_inventory FOREIGN KEY (tenant_id, inventory_id)
    REFERENCES pharmacy.pharmacy_inventory (tenant_id, id) ON DELETE SET NULL;
ALTER TABLE pharmacy.dispense_items
    ADD CONSTRAINT fk_dispense_items_rx_item FOREIGN KEY (tenant_id, prescription_item_id)
    REFERENCES clinical.opd_prescription_items (tenant_id, id);
CREATE INDEX idx_dispense_items_tenant_id ON pharmacy.dispense_items (tenant_id);
CREATE INDEX idx_dispense_items_tenant_active ON pharmacy.dispense_items (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE pharmacy.pharmacy_stock_movements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    medicine_id         UUID NOT NULL,
    inventory_id        UUID,
    movement_type       VARCHAR(20) NOT NULL
                        CHECK (movement_type IN ('purchase', 'dispense', 'adjustment', 'return', 'expired')),
    quantity            INTEGER NOT NULL,
    reference_type      VARCHAR(30) CHECK (reference_type IN ('dispense', 'purchase_order', 'manual')),
    reference_id        UUID,
    notes               TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID
);
COMMENT ON TABLE pharmacy.pharmacy_stock_movements IS 'Immutable append-only pharmacy stock ledger.';
CREATE UNIQUE INDEX uq_pharmacy_stock_movements_tenant_id_id ON pharmacy.pharmacy_stock_movements (tenant_id, id);
ALTER TABLE pharmacy.pharmacy_stock_movements
    ADD CONSTRAINT fk_stock_mov_medicine FOREIGN KEY (tenant_id, medicine_id)
    REFERENCES pharmacy.medicines (tenant_id, id);
ALTER TABLE pharmacy.pharmacy_stock_movements
    ADD CONSTRAINT fk_stock_mov_inventory FOREIGN KEY (tenant_id, inventory_id)
    REFERENCES pharmacy.pharmacy_inventory (tenant_id, id);
CREATE INDEX idx_pharmacy_stock_movements_med_date ON pharmacy.pharmacy_stock_movements (tenant_id, medicine_id, created_at);
CREATE INDEX idx_pharmacy_stock_movements_tenant_id ON pharmacy.pharmacy_stock_movements (tenant_id);

-- =============================================================================
-- LABORATORY SCHEMA
-- =============================================================================
CREATE TABLE laboratory.lab_test_catalog (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    code                VARCHAR(20) NOT NULL,
    name                VARCHAR(255) NOT NULL,
    category            VARCHAR(50) NOT NULL,
    sample_type           VARCHAR(50) NOT NULL,
    price               DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    tat_hours           INTEGER CHECK (tat_hours IS NULL OR tat_hours > 0),
    normal_range        TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_test_catalog IS 'Laboratory test definitions and pricing.';
CREATE UNIQUE INDEX uq_lab_test_catalog_tenant_id_id ON laboratory.lab_test_catalog (tenant_id, id);
CREATE UNIQUE INDEX uq_lab_test_catalog_tenant_code ON laboratory.lab_test_catalog (tenant_id, code);
CREATE INDEX idx_lab_test_catalog_tenant_id ON laboratory.lab_test_catalog (tenant_id);
CREATE INDEX idx_lab_test_catalog_tenant_active ON laboratory.lab_test_catalog (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE laboratory.lab_orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    order_number        VARCHAR(20) NOT NULL,
    patient_id          UUID NOT NULL,
    ordering_doctor_id  UUID,
    opd_visit_id        UUID,
    admission_id        UUID,
    order_date          TIMESTAMPTZ NOT NULL,
    priority            VARCHAR(10) NOT NULL DEFAULT 'routine' CHECK (priority IN ('routine', 'urgent', 'stat')),
    status              VARCHAR(20) NOT NULL DEFAULT 'ordered'
                        CHECK (status IN ('ordered', 'sample_collected', 'processing', 'completed', 'cancelled')),
    clinical_notes      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_orders IS 'Laboratory order headers.';
CREATE UNIQUE INDEX uq_lab_orders_tenant_id_id ON laboratory.lab_orders (tenant_id, id);
ALTER TABLE laboratory.lab_orders
    ADD CONSTRAINT fk_lab_orders_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE laboratory.lab_orders
    ADD CONSTRAINT fk_lab_orders_doctor FOREIGN KEY (tenant_id, ordering_doctor_id)
    REFERENCES core.doctors (tenant_id, id);
ALTER TABLE laboratory.lab_orders
    ADD CONSTRAINT fk_lab_orders_opd FOREIGN KEY (tenant_id, opd_visit_id)
    REFERENCES clinical.opd_visits (tenant_id, id);
ALTER TABLE laboratory.lab_orders
    ADD CONSTRAINT fk_lab_orders_admission FOREIGN KEY (tenant_id, admission_id)
    REFERENCES clinical.admissions (tenant_id, id);
CREATE UNIQUE INDEX uq_lab_orders_tenant_number ON laboratory.lab_orders (tenant_id, order_number);
CREATE INDEX idx_lab_orders_patient ON laboratory.lab_orders (tenant_id, patient_id);
CREATE INDEX idx_lab_orders_status ON laboratory.lab_orders (tenant_id, status, order_date);
CREATE INDEX idx_lab_orders_tenant_id ON laboratory.lab_orders (tenant_id);
CREATE INDEX idx_lab_orders_tenant_active ON laboratory.lab_orders (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE laboratory.lab_order_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    lab_order_id        UUID NOT NULL,
    test_id             UUID NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'ordered'
                        CHECK (status IN ('ordered', 'sample_collected', 'processing', 'completed', 'cancelled')),
    price               DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_order_items IS 'Individual tests on laboratory orders.';
CREATE UNIQUE INDEX uq_lab_order_items_tenant_id_id ON laboratory.lab_order_items (tenant_id, id);
ALTER TABLE laboratory.lab_order_items
    ADD CONSTRAINT fk_lab_order_items_order FOREIGN KEY (tenant_id, lab_order_id)
    REFERENCES laboratory.lab_orders (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE laboratory.lab_order_items
    ADD CONSTRAINT fk_lab_order_items_test FOREIGN KEY (tenant_id, test_id)
    REFERENCES laboratory.lab_test_catalog (tenant_id, id);
CREATE INDEX idx_lab_order_items_tenant_id ON laboratory.lab_order_items (tenant_id);
CREATE INDEX idx_lab_order_items_tenant_active ON laboratory.lab_order_items (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE laboratory.lab_samples (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    sample_id           VARCHAR(30) NOT NULL,
    lab_order_item_id   UUID NOT NULL,
    sample_type         VARCHAR(50) NOT NULL,
    collected_at        TIMESTAMPTZ,
    collected_by        UUID,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'collected', 'processing', 'completed', 'rejected')),
    rejection_reason    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_samples IS 'Sample collection and tracking for lab tests.';
CREATE UNIQUE INDEX uq_lab_samples_tenant_id_id ON laboratory.lab_samples (tenant_id, id);
ALTER TABLE laboratory.lab_samples
    ADD CONSTRAINT fk_lab_samples_order_item FOREIGN KEY (tenant_id, lab_order_item_id)
    REFERENCES laboratory.lab_order_items (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE laboratory.lab_samples
    ADD CONSTRAINT fk_lab_samples_collector FOREIGN KEY (tenant_id, collected_by)
    REFERENCES core.staff (tenant_id, id);
CREATE UNIQUE INDEX uq_lab_samples_tenant_sample_id ON laboratory.lab_samples (tenant_id, sample_id);
CREATE INDEX idx_lab_samples_tenant_id ON laboratory.lab_samples (tenant_id);
CREATE INDEX idx_lab_samples_tenant_active ON laboratory.lab_samples (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE laboratory.lab_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    lab_order_item_id   UUID NOT NULL,
    sample_id           UUID,
    parameter_name      VARCHAR(150) NOT NULL,
    result_value        VARCHAR(255) NOT NULL,
    unit                VARCHAR(30),
    reference_range     VARCHAR(100),
    is_abnormal         BOOLEAN NOT NULL DEFAULT FALSE,
    is_critical         BOOLEAN NOT NULL DEFAULT FALSE,
    entered_by          UUID,
    entered_at          TIMESTAMPTZ NOT NULL,
    verified_by         UUID,
    verified_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_results IS 'Result values per laboratory test item.';
CREATE UNIQUE INDEX uq_lab_results_tenant_id_id ON laboratory.lab_results (tenant_id, id);
ALTER TABLE laboratory.lab_results
    ADD CONSTRAINT fk_lab_results_order_item FOREIGN KEY (tenant_id, lab_order_item_id)
    REFERENCES laboratory.lab_order_items (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE laboratory.lab_results
    ADD CONSTRAINT fk_lab_results_sample FOREIGN KEY (tenant_id, sample_id)
    REFERENCES laboratory.lab_samples (tenant_id, id);
ALTER TABLE laboratory.lab_results
    ADD CONSTRAINT fk_lab_results_entered_by FOREIGN KEY (tenant_id, entered_by)
    REFERENCES core.staff (tenant_id, id);
ALTER TABLE laboratory.lab_results
    ADD CONSTRAINT fk_lab_results_verified_by FOREIGN KEY (tenant_id, verified_by)
    REFERENCES core.staff (tenant_id, id);
CREATE INDEX idx_lab_results_critical ON laboratory.lab_results (tenant_id, is_critical) WHERE is_critical = TRUE;
CREATE INDEX idx_lab_results_tenant_id ON laboratory.lab_results (tenant_id);
CREATE INDEX idx_lab_results_tenant_active ON laboratory.lab_results (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE laboratory.lab_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    report_number       VARCHAR(20) NOT NULL,
    lab_order_id        UUID NOT NULL,
    patient_id          UUID NOT NULL,
    report_date         TIMESTAMPTZ NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'finalized', 'amended')),
    file_path           TEXT,
    finalized_by        UUID,
    finalized_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_reports IS 'Finalized laboratory report documents.';
CREATE UNIQUE INDEX uq_lab_reports_tenant_id_id ON laboratory.lab_reports (tenant_id, id);
ALTER TABLE laboratory.lab_reports
    ADD CONSTRAINT fk_lab_reports_order FOREIGN KEY (tenant_id, lab_order_id)
    REFERENCES laboratory.lab_orders (tenant_id, id);
ALTER TABLE laboratory.lab_reports
    ADD CONSTRAINT fk_lab_reports_patient FOREIGN KEY (tenant_id, patient_id)
    REFERENCES core.patients (tenant_id, id);
ALTER TABLE laboratory.lab_reports
    ADD CONSTRAINT fk_lab_reports_finalized_by FOREIGN KEY (tenant_id, finalized_by)
    REFERENCES core.staff (tenant_id, id);
CREATE UNIQUE INDEX uq_lab_reports_tenant_number ON laboratory.lab_reports (tenant_id, report_number);
CREATE INDEX idx_lab_reports_tenant_id ON laboratory.lab_reports (tenant_id);
CREATE INDEX idx_lab_reports_tenant_active ON laboratory.lab_reports (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE laboratory.lab_report_signatures (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    lab_report_id       UUID NOT NULL,
    staff_id            UUID NOT NULL,
    designation         VARCHAR(100) NOT NULL,
    signed_at           TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE laboratory.lab_report_signatures IS 'Authorized signatories on laboratory reports.';
CREATE UNIQUE INDEX uq_lab_report_signatures_tenant_id_id ON laboratory.lab_report_signatures (tenant_id, id);
ALTER TABLE laboratory.lab_report_signatures
    ADD CONSTRAINT fk_lab_report_sigs_report FOREIGN KEY (tenant_id, lab_report_id)
    REFERENCES laboratory.lab_reports (tenant_id, id) ON DELETE CASCADE;
ALTER TABLE laboratory.lab_report_signatures
    ADD CONSTRAINT fk_lab_report_sigs_staff FOREIGN KEY (tenant_id, staff_id)
    REFERENCES core.staff (tenant_id, id);
CREATE INDEX idx_lab_report_signatures_tenant_id ON laboratory.lab_report_signatures (tenant_id);
CREATE INDEX idx_lab_report_signatures_tenant_active ON laboratory.lab_report_signatures (tenant_id) WHERE deleted_at IS NULL;

-- =============================================================================
-- COMMS SCHEMA
-- =============================================================================
CREATE TABLE comms.notification_templates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    code                VARCHAR(50) NOT NULL,
    channel             VARCHAR(10) NOT NULL CHECK (channel IN ('email', 'sms', 'in_app')),
    subject             VARCHAR(255),
    body_template       TEXT NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE comms.notification_templates IS 'Email, SMS, and in-app notification templates.';
CREATE UNIQUE INDEX uq_notification_templates_tenant_id_id ON comms.notification_templates (tenant_id, id);
CREATE UNIQUE INDEX uq_notification_templates_tenant_code ON comms.notification_templates (tenant_id, code, channel);
CREATE INDEX idx_notification_templates_tenant_id ON comms.notification_templates (tenant_id);
CREATE INDEX idx_notification_templates_tenant_active ON comms.notification_templates (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE comms.notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    user_id             UUID NOT NULL,
    title               VARCHAR(255) NOT NULL,
    message             TEXT NOT NULL,
    notification_type   VARCHAR(50) NOT NULL,
    reference_type      VARCHAR(30),
    reference_id        UUID,
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    read_at             TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE comms.notifications IS 'In-app notifications for users.';
CREATE UNIQUE INDEX uq_notifications_tenant_id_id ON comms.notifications (tenant_id, id);
ALTER TABLE comms.notifications
    ADD CONSTRAINT fk_notifications_user FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id) ON DELETE CASCADE;
CREATE INDEX idx_notifications_user_unread ON comms.notifications (tenant_id, user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_tenant_id ON comms.notifications (tenant_id);
CREATE INDEX idx_notifications_tenant_active ON comms.notifications (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE comms.notification_preferences (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    user_id             UUID NOT NULL,
    notification_type   VARCHAR(50) NOT NULL,
    channel             VARCHAR(10) NOT NULL CHECK (channel IN ('email', 'sms', 'in_app')),
    is_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_at      TIMESTAMPTZ,
    updated_by      UUID,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1
);
COMMENT ON TABLE comms.notification_preferences IS 'Per-user notification channel preferences.';
CREATE UNIQUE INDEX uq_notification_preferences_tenant_id_id ON comms.notification_preferences (tenant_id, id);
ALTER TABLE comms.notification_preferences
    ADD CONSTRAINT fk_notif_prefs_user FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id) ON DELETE CASCADE;
CREATE UNIQUE INDEX uq_notification_preferences ON comms.notification_preferences (tenant_id, user_id, notification_type, channel);
CREATE INDEX idx_notification_preferences_tenant_id ON comms.notification_preferences (tenant_id);
CREATE INDEX idx_notification_preferences_tenant_active ON comms.notification_preferences (tenant_id) WHERE deleted_at IS NULL;
CREATE TABLE comms.notification_delivery_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    notification_id     UUID,
    recipient           VARCHAR(255) NOT NULL,
    channel             VARCHAR(10) NOT NULL CHECK (channel IN ('email', 'sms')),
    template_code       VARCHAR(50),
    status              VARCHAR(20) NOT NULL CHECK (status IN ('sent', 'delivered', 'failed', 'bounced')),
    provider_message_id VARCHAR(255),
    error_message       TEXT,
    sent_at             TIMESTAMPTZ NOT NULL,
    delivered_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID
);
COMMENT ON TABLE comms.notification_delivery_log IS 'Immutable external notification delivery tracking.';
CREATE UNIQUE INDEX uq_notification_delivery_log_tenant_id_id ON comms.notification_delivery_log (tenant_id, id);
ALTER TABLE comms.notification_delivery_log
    ADD CONSTRAINT fk_notif_delivery_notification FOREIGN KEY (tenant_id, notification_id)
    REFERENCES comms.notifications (tenant_id, id);
CREATE INDEX idx_notification_delivery_log_tenant_id ON comms.notification_delivery_log (tenant_id);
CREATE INDEX idx_notification_delivery_log_sent ON comms.notification_delivery_log (tenant_id, sent_at);

-- =============================================================================
-- AUDIT SCHEMA
-- =============================================================================
CREATE TABLE audit.audit_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES platform.tenants(id),
    user_id             UUID,
    action              VARCHAR(50) NOT NULL
                        CHECK (action IN ('create', 'update', 'delete', 'login', 'logout', 'export', 'view')),
    entity_type         VARCHAR(50) NOT NULL,
    entity_id           UUID,
    old_values          JSONB,
    new_values          JSONB,
    ip_address          INET,
    user_agent          TEXT,
    request_id          UUID,
    metadata            JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID
);
COMMENT ON TABLE audit.audit_logs IS 'Immutable security and data mutation audit trail.';
CREATE UNIQUE INDEX uq_audit_logs_tenant_id_id ON audit.audit_logs (tenant_id, id);
ALTER TABLE audit.audit_logs
    ADD CONSTRAINT fk_audit_logs_user FOREIGN KEY (tenant_id, user_id)
    REFERENCES core.users (tenant_id, id);
CREATE INDEX idx_audit_logs_tenant_entity ON audit.audit_logs (tenant_id, entity_type, entity_id);
CREATE INDEX idx_audit_logs_tenant_user ON audit.audit_logs (tenant_id, user_id, created_at);
CREATE INDEX idx_audit_logs_created_brin ON audit.audit_logs USING BRIN (created_at);
CREATE INDEX idx_audit_logs_tenant_id ON audit.audit_logs (tenant_id);

-- =============================================================================
-- TRIGGERS: set_updated_at on mutable tables
-- =============================================================================
CREATE TRIGGER trg_subscription_plans_updated_at BEFORE UPDATE ON platform.subscription_plans
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_tenant_locations_updated_at BEFORE UPDATE ON platform.tenant_locations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_tenant_subscriptions_updated_at BEFORE UPDATE ON platform.tenant_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_tenant_settings_updated_at BEFORE UPDATE ON platform.tenant_settings
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_roles_updated_at BEFORE UPDATE ON core.roles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_permissions_updated_at BEFORE UPDATE ON core.permissions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_departments_updated_at BEFORE UPDATE ON core.departments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_staff_updated_at BEFORE UPDATE ON core.staff
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON core.users
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_role_permissions_updated_at BEFORE UPDATE ON core.role_permissions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_user_roles_updated_at BEFORE UPDATE ON core.user_roles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_user_sessions_updated_at BEFORE UPDATE ON core.user_sessions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_password_reset_tokens_updated_at BEFORE UPDATE ON core.password_reset_tokens
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_patients_updated_at BEFORE UPDATE ON core.patients
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_patient_allergies_updated_at BEFORE UPDATE ON core.patient_allergies
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_patient_contacts_updated_at BEFORE UPDATE ON core.patient_contacts
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_patient_documents_updated_at BEFORE UPDATE ON core.patient_documents
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_doctors_updated_at BEFORE UPDATE ON core.doctors
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_doctor_schedules_updated_at BEFORE UPDATE ON core.doctor_schedules
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_appointments_updated_at BEFORE UPDATE ON clinical.appointments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_visits_updated_at BEFORE UPDATE ON clinical.opd_visits
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_queue_updated_at BEFORE UPDATE ON clinical.opd_queue
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_vitals_updated_at BEFORE UPDATE ON clinical.opd_vitals
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_clinical_notes_updated_at BEFORE UPDATE ON clinical.opd_clinical_notes
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_medicines_updated_at BEFORE UPDATE ON pharmacy.medicines
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_prescriptions_updated_at BEFORE UPDATE ON clinical.opd_prescriptions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_prescription_items_updated_at BEFORE UPDATE ON clinical.opd_prescription_items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_opd_referrals_updated_at BEFORE UPDATE ON clinical.opd_referrals
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_wards_updated_at BEFORE UPDATE ON clinical.wards
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_rooms_updated_at BEFORE UPDATE ON clinical.rooms
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_beds_updated_at BEFORE UPDATE ON clinical.beds
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_admissions_updated_at BEFORE UPDATE ON clinical.admissions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_admission_transfers_updated_at BEFORE UPDATE ON clinical.admission_transfers
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_nursing_notes_updated_at BEFORE UPDATE ON clinical.nursing_notes
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_ipd_vitals_updated_at BEFORE UPDATE ON clinical.ipd_vitals
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_discharge_summaries_updated_at BEFORE UPDATE ON clinical.discharge_summaries
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_billing_services_updated_at BEFORE UPDATE ON billing.billing_services
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_invoices_updated_at BEFORE UPDATE ON billing.invoices
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_ipd_daily_charges_updated_at BEFORE UPDATE ON clinical.ipd_daily_charges
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_invoice_line_items_updated_at BEFORE UPDATE ON billing.invoice_line_items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_payments_updated_at BEFORE UPDATE ON billing.payments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_payment_allocations_updated_at BEFORE UPDATE ON billing.payment_allocations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_invoice_adjustments_updated_at BEFORE UPDATE ON billing.invoice_adjustments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_pharmacy_inventory_updated_at BEFORE UPDATE ON pharmacy.pharmacy_inventory
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_purchase_orders_updated_at BEFORE UPDATE ON pharmacy.purchase_orders
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_dispense_records_updated_at BEFORE UPDATE ON pharmacy.dispense_records
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_dispense_items_updated_at BEFORE UPDATE ON pharmacy.dispense_items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_test_catalog_updated_at BEFORE UPDATE ON laboratory.lab_test_catalog
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_orders_updated_at BEFORE UPDATE ON laboratory.lab_orders
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_order_items_updated_at BEFORE UPDATE ON laboratory.lab_order_items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_samples_updated_at BEFORE UPDATE ON laboratory.lab_samples
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_results_updated_at BEFORE UPDATE ON laboratory.lab_results
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_reports_updated_at BEFORE UPDATE ON laboratory.lab_reports
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_lab_report_signatures_updated_at BEFORE UPDATE ON laboratory.lab_report_signatures
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_notification_templates_updated_at BEFORE UPDATE ON comms.notification_templates
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_notifications_updated_at BEFORE UPDATE ON comms.notifications
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trg_notification_preferences_updated_at BEFORE UPDATE ON comms.notification_preferences
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- =============================================================================
-- ROW-LEVEL SECURITY
-- =============================================================================
ALTER TABLE platform.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.tenants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON platform.tenants FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON platform.tenants FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON platform.tenants FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON platform.tenants FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE platform.subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.subscription_plans FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON platform.subscription_plans FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON platform.subscription_plans FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON platform.subscription_plans FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON platform.subscription_plans FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE platform.tenant_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.tenant_locations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON platform.tenant_locations FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON platform.tenant_locations FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON platform.tenant_locations FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON platform.tenant_locations FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE platform.tenant_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.tenant_subscriptions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON platform.tenant_subscriptions FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON platform.tenant_subscriptions FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON platform.tenant_subscriptions FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON platform.tenant_subscriptions FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE platform.tenant_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform.tenant_settings FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON platform.tenant_settings FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON platform.tenant_settings FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON platform.tenant_settings FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON platform.tenant_settings FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.roles FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.roles FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.roles FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.roles FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.roles FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.permissions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.permissions FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.permissions FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.permissions FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.permissions FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.departments FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.departments FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.departments FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.departments FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.departments FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.staff ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.staff FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.staff FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.staff FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.staff FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.staff FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.users FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.users FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.users FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.users FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.users FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.role_permissions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.role_permissions FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.role_permissions FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.role_permissions FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.role_permissions FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_roles FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.user_roles FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.user_roles FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.user_roles FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.user_roles FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.user_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.user_sessions FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.user_sessions FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.user_sessions FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.user_sessions FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.password_reset_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.password_reset_tokens FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.password_reset_tokens FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.password_reset_tokens FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.password_reset_tokens FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.password_reset_tokens FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.patients FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.patients FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.patients FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.patients FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.patients FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.patient_allergies ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.patient_allergies FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.patient_allergies FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.patient_allergies FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.patient_allergies FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.patient_allergies FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.patient_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.patient_contacts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.patient_contacts FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.patient_contacts FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.patient_contacts FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.patient_contacts FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.patient_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.patient_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.patient_documents FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.patient_documents FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.patient_documents FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.patient_documents FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.doctors FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.doctors FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.doctors FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.doctors FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.doctors FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE core.doctor_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE core.doctor_schedules FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON core.doctor_schedules FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON core.doctor_schedules FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON core.doctor_schedules FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON core.doctor_schedules FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.appointments FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.appointments FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.appointments FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.appointments FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.appointments FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_visits FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_visits FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_visits FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_visits FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_visits FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_queue FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_queue FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_queue FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_queue FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_queue FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_vitals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_vitals FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_vitals FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_vitals FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_vitals FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_clinical_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_clinical_notes FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_clinical_notes FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_clinical_notes FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_clinical_notes FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_clinical_notes FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE pharmacy.medicines ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy.medicines FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON pharmacy.medicines FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON pharmacy.medicines FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON pharmacy.medicines FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON pharmacy.medicines FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_prescriptions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_prescriptions FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_prescriptions FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_prescriptions FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_prescriptions FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_prescription_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_prescription_items FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_prescription_items FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_prescription_items FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_prescription_items FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_prescription_items FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.opd_referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.opd_referrals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.opd_referrals FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.opd_referrals FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.opd_referrals FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.opd_referrals FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.wards ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.wards FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.wards FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.wards FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.wards FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.wards FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.rooms FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.rooms FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.rooms FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.rooms FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.rooms FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.beds ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.beds FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.beds FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.beds FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.beds FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.beds FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.admissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.admissions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.admissions FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.admissions FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.admissions FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.admissions FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.admission_transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.admission_transfers FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.admission_transfers FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.admission_transfers FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.admission_transfers FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.admission_transfers FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.nursing_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.nursing_notes FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.nursing_notes FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.nursing_notes FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.nursing_notes FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.nursing_notes FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.ipd_vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.ipd_vitals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.ipd_vitals FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.ipd_vitals FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.ipd_vitals FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.ipd_vitals FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.discharge_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.discharge_summaries FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.discharge_summaries FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.discharge_summaries FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.discharge_summaries FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.discharge_summaries FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE billing.billing_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing.billing_services FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON billing.billing_services FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON billing.billing_services FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON billing.billing_services FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON billing.billing_services FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE billing.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing.invoices FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON billing.invoices FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON billing.invoices FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON billing.invoices FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON billing.invoices FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE clinical.ipd_daily_charges ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical.ipd_daily_charges FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON clinical.ipd_daily_charges FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON clinical.ipd_daily_charges FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON clinical.ipd_daily_charges FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON clinical.ipd_daily_charges FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE billing.invoice_line_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing.invoice_line_items FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON billing.invoice_line_items FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON billing.invoice_line_items FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON billing.invoice_line_items FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON billing.invoice_line_items FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE billing.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing.payments FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON billing.payments FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON billing.payments FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON billing.payments FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON billing.payments FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE billing.payment_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing.payment_allocations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON billing.payment_allocations FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON billing.payment_allocations FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON billing.payment_allocations FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON billing.payment_allocations FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE billing.invoice_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing.invoice_adjustments FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON billing.invoice_adjustments FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON billing.invoice_adjustments FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON billing.invoice_adjustments FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON billing.invoice_adjustments FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE pharmacy.pharmacy_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy.pharmacy_inventory FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON pharmacy.pharmacy_inventory FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON pharmacy.pharmacy_inventory FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON pharmacy.pharmacy_inventory FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON pharmacy.pharmacy_inventory FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE pharmacy.purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy.purchase_orders FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON pharmacy.purchase_orders FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON pharmacy.purchase_orders FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON pharmacy.purchase_orders FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON pharmacy.purchase_orders FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE pharmacy.dispense_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy.dispense_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON pharmacy.dispense_records FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON pharmacy.dispense_records FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON pharmacy.dispense_records FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON pharmacy.dispense_records FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE pharmacy.dispense_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy.dispense_items FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON pharmacy.dispense_items FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON pharmacy.dispense_items FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON pharmacy.dispense_items FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON pharmacy.dispense_items FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_test_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_test_catalog FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_test_catalog FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_test_catalog FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_test_catalog FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_test_catalog FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_orders FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_orders FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_orders FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_orders FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_orders FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_order_items FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_order_items FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_order_items FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_order_items FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_order_items FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_samples ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_samples FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_samples FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_samples FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_samples FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_samples FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_results FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_results FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_results FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_results FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_results FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_reports FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_reports FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_reports FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_reports FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_reports FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE laboratory.lab_report_signatures ENABLE ROW LEVEL SECURITY;
ALTER TABLE laboratory.lab_report_signatures FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON laboratory.lab_report_signatures FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON laboratory.lab_report_signatures FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON laboratory.lab_report_signatures FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON laboratory.lab_report_signatures FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE comms.notification_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE comms.notification_templates FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON comms.notification_templates FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON comms.notification_templates FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON comms.notification_templates FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON comms.notification_templates FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE comms.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE comms.notifications FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON comms.notifications FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON comms.notifications FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON comms.notifications FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON comms.notifications FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE comms.notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE comms.notification_preferences FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON comms.notification_preferences FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON comms.notification_preferences FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON comms.notification_preferences FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON comms.notification_preferences FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE pharmacy.pharmacy_stock_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE pharmacy.pharmacy_stock_movements FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON pharmacy.pharmacy_stock_movements FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON pharmacy.pharmacy_stock_movements FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON pharmacy.pharmacy_stock_movements FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON pharmacy.pharmacy_stock_movements FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE comms.notification_delivery_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE comms.notification_delivery_log FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON comms.notification_delivery_log FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON comms.notification_delivery_log FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON comms.notification_delivery_log FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON comms.notification_delivery_log FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
ALTER TABLE audit.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.audit_logs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_select ON audit.audit_logs FOR SELECT USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_insert ON audit.audit_logs FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_update ON audit.audit_logs FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', true)::uuid) WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_isolation_delete ON audit.audit_logs FOR DELETE USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- =============================================================================
-- BOOTSTRAP: tenant provisioning helper
-- =============================================================================
-- First tenant insert requires id = tenant_id. Use this function or set both
-- explicitly inside a deferred transaction.
CREATE OR REPLACE FUNCTION platform.create_tenant(
    p_name        VARCHAR(255),
    p_slug        VARCHAR(100),
    p_email       VARCHAR(255),
    p_country     VARCHAR(100) DEFAULT 'IN',
    p_timezone    VARCHAR(50) DEFAULT 'Asia/Kolkata',
    p_currency    VARCHAR(3) DEFAULT 'INR'
)
RETURNS UUID AS $$
DECLARE
    v_tenant_id UUID := gen_random_uuid();
BEGIN
    INSERT INTO platform.tenants (
        id, tenant_id, name, slug, email, country, timezone, currency, status
    ) VALUES (
        v_tenant_id, v_tenant_id, p_name, p_slug, p_email, p_country, p_timezone, p_currency, 'trial'
    );
    RETURN v_tenant_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION platform.create_tenant IS
    'Creates a tenant root row with tenant_id = id (required for self-referencing FK).';
