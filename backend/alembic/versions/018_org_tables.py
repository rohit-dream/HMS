"""MVP-059 — core org tables: departments, staff, doctors, doctor_schedules + RLS.

Sprint 6 logical migration: 005_org_tables

Revision ID: 018_org_tables
Revises: 017_tenant_status_past_due
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    CORE_ORG_RLS_TABLES,
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "018_org_tables"
down_revision: str | None = "017_tenant_status_past_due"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE core.departments (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            name            VARCHAR(150) NOT NULL,
            code            VARCHAR(20) NOT NULL,
            head_staff_id   UUID,
            location_id     UUID,
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
    op.execute("COMMENT ON TABLE core.departments IS 'Hospital departments.'")
    op.execute(
        "CREATE UNIQUE INDEX uq_departments_tenant_id_id ON core.departments (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.departments
            ADD CONSTRAINT fk_departments_location
            FOREIGN KEY (tenant_id, location_id)
            REFERENCES platform.tenant_locations (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_departments_tenant_code ON core.departments (tenant_id, code)"
    )
    op.execute("CREATE INDEX idx_departments_tenant_id ON core.departments (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_departments_tenant_active
        ON core.departments (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE core.staff (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            employee_code   VARCHAR(20) NOT NULL,
            first_name      VARCHAR(100) NOT NULL,
            last_name       VARCHAR(100) NOT NULL,
            email           VARCHAR(255),
            phone           VARCHAR(20),
            department_id   UUID,
            designation     VARCHAR(100),
            joining_date    DATE NOT NULL,
            leaving_date    DATE,
            status          VARCHAR(20) NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'on_leave', 'terminated')),
            location_id     UUID,
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
    op.execute("COMMENT ON TABLE core.staff IS 'Employee records.'")
    op.execute("CREATE UNIQUE INDEX uq_staff_tenant_id_id ON core.staff (tenant_id, id)")
    op.execute(
        """
        ALTER TABLE core.staff
            ADD CONSTRAINT fk_staff_department
            FOREIGN KEY (tenant_id, department_id)
            REFERENCES core.departments (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE core.staff
            ADD CONSTRAINT fk_staff_location
            FOREIGN KEY (tenant_id, location_id)
            REFERENCES platform.tenant_locations (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE core.departments
            ADD CONSTRAINT fk_departments_head_staff
            FOREIGN KEY (tenant_id, head_staff_id)
            REFERENCES core.staff (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_staff_tenant_code ON core.staff (tenant_id, employee_code)"
    )
    op.execute("CREATE INDEX idx_staff_tenant_id ON core.staff (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_staff_tenant_active
        ON core.staff (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
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
    op.execute("COMMENT ON TABLE core.doctors IS 'Doctor profiles extending staff records.'")
    op.execute("CREATE UNIQUE INDEX uq_doctors_tenant_id_id ON core.doctors (tenant_id, id)")
    op.execute(
        """
        ALTER TABLE core.doctors
            ADD CONSTRAINT fk_doctors_staff
            FOREIGN KEY (tenant_id, staff_id)
            REFERENCES core.staff (tenant_id, id)
        """
    )
    op.execute(
        """
        ALTER TABLE core.doctors
            ADD CONSTRAINT fk_doctors_department
            FOREIGN KEY (tenant_id, department_id)
            REFERENCES core.departments (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_doctors_tenant_staff ON core.doctors (tenant_id, staff_id)"
    )
    op.execute("CREATE INDEX idx_doctors_tenant_id ON core.doctors (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_doctors_tenant_active
        ON core.doctors (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE core.doctor_schedules (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id               UUID NOT NULL REFERENCES platform.tenants(id),
            doctor_id               UUID NOT NULL,
            day_of_week             SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
            start_time              TIME NOT NULL,
            end_time                TIME NOT NULL,
            slot_duration_minutes   INTEGER NOT NULL CHECK (slot_duration_minutes > 0),
            max_patients_per_slot   INTEGER NOT NULL DEFAULT 1 CHECK (max_patients_per_slot > 0),
            location_id             UUID,
            is_active               BOOLEAN NOT NULL DEFAULT TRUE,
            CHECK (end_time > start_time),
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by              UUID,
            updated_at              TIMESTAMPTZ,
            updated_by              UUID,
            deleted_at              TIMESTAMPTZ,
            deleted_by              UUID,
            version                 INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE core.doctor_schedules IS "
        "'Doctor availability schedules and appointment slots.'"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_doctor_schedules_tenant_id_id "
        "ON core.doctor_schedules (tenant_id, id)"
    )
    op.execute(
        """
        ALTER TABLE core.doctor_schedules
            ADD CONSTRAINT fk_doctor_schedules_doctor
            FOREIGN KEY (tenant_id, doctor_id)
            REFERENCES core.doctors (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        ALTER TABLE core.doctor_schedules
            ADD CONSTRAINT fk_doctor_schedules_location
            FOREIGN KEY (tenant_id, location_id)
            REFERENCES platform.tenant_locations (tenant_id, id)
        """
    )
    op.execute("CREATE INDEX idx_doctor_schedules_tenant_id ON core.doctor_schedules (tenant_id)")
    op.execute(
        """
        CREATE INDEX idx_doctor_schedules_tenant_active
        ON core.doctor_schedules (tenant_id) WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        ALTER TABLE core.users
            ADD CONSTRAINT fk_users_staff
            FOREIGN KEY (tenant_id, staff_id)
            REFERENCES core.staff (tenant_id, id) ON DELETE SET NULL
        """
    )

    for table in ("departments", "staff", "doctors", "doctor_schedules"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at BEFORE UPDATE ON core.{table}
                FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
            """
        )

    for table in CORE_ORG_RLS_TABLES:
        for stmt in enable_rls_statements("core", table):
            op.execute(stmt)
        for stmt in tenant_isolation_policy_statements("core", table):
            op.execute(stmt)

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO hms_app"
    )


def downgrade() -> None:
    for table in reversed(CORE_ORG_RLS_TABLES):
        for stmt in disable_rls_statements("core", table):
            op.execute(stmt)

    op.execute("ALTER TABLE core.users DROP CONSTRAINT IF EXISTS fk_users_staff")
    op.execute("DROP TABLE IF EXISTS core.doctor_schedules CASCADE")
    op.execute("DROP TABLE IF EXISTS core.doctors CASCADE")
    op.execute("DROP TABLE IF EXISTS core.staff CASCADE")
    op.execute("DROP TABLE IF EXISTS core.departments CASCADE")
