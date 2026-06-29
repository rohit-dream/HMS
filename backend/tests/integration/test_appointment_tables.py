"""Integration tests — MVP-083 clinical.appointments table + RLS."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CLINICAL_APPOINTMENT_RLS_TABLES
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]

APPOINTMENT_COLUMNS = (
    "id",
    "tenant_id",
    "patient_id",
    "doctor_id",
    "location_id",
    "appointment_date",
    "start_time",
    "end_time",
    "appointment_type",
    "status",
    "is_walk_in",
    "notes",
    "cancelled_reason",
    "reminder_sent_at",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "deleted_at",
    "deleted_by",
    "version",
)


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _insert_patient(
    db,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    mrn: str,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO core.patients (
                id, tenant_id, mrn, first_name, last_name,
                date_of_birth, gender, phone
            ) VALUES (
                :id, :tenant_id, :mrn, 'Anita', 'Sharma',
                :dob, 'female', '9876543210'
            )
            """
        ),
        {
            "id": patient_id,
            "tenant_id": tenant_id,
            "mrn": mrn,
            "dob": date(1990, 5, 15),
        },
    )


def _provision_doctor(db, tenant_id: uuid.UUID) -> uuid.UUID:
    suffix = tenant_id.hex[:6].upper()
    dept = DepartmentRepository(db, tenant_id).create(
        name="General Medicine",
        code=f"GM-{suffix}",
        is_active=True,
    )
    staff = StaffRepository(db, tenant_id).create(
        employee_code=f"DOC-{suffix}",
        first_name="Vikram",
        last_name="Patel",
        joining_date=date.today(),
        status="active",
        department_id=dept.id,
    )
    db.flush()
    doctor = DoctorRepository(db, tenant_id).create(
        staff_id=staff.id,
        specialization="General Medicine",
        consultation_fee=Decimal("500.00"),
        department_id=dept.id,
    )
    db.flush()
    return doctor.id


def _insert_appointment(
    db,
    *,
    tenant_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    appointment_date: date | None = None,
    start_time: time = time(9, 0),
    end_time: time = time(9, 20),
    status: str = "scheduled",
    is_walk_in: bool = False,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO clinical.appointments (
                id, tenant_id, patient_id, doctor_id,
                appointment_date, start_time, end_time,
                appointment_type, status, is_walk_in
            ) VALUES (
                :id, :tenant_id, :patient_id, :doctor_id,
                :appointment_date, :start_time, :end_time,
                'new', :status, :is_walk_in
            )
            """
        ),
        {
            "id": appointment_id,
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_date": appointment_date or date.today(),
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
            "is_walk_in": is_walk_in,
        },
    )


@pytest.mark.integration
def test_appointment_table_exists_with_expected_columns() -> None:
    """Migration 025 must create clinical.appointments with required columns."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'clinical' AND table_name = 'appointments'
                    )
                    """
                )
            ).scalar_one()
            assert exists is True

            columns = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'clinical' AND table_name = 'appointments'
                        """
                    )
                )
            }
            for column in APPOINTMENT_COLUMNS:
                assert column in columns, f"Missing column: {column}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_appointment_table_rls_enabled_with_policies() -> None:
    """clinical.appointments must have FORCE RLS and four tenant isolation policies."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in CLINICAL_APPOINTMENT_RLS_TABLES:
                rls_enabled = conn.execute(
                    text(
                        """
                        SELECT c.relrowsecurity AND c.relforcerowsecurity
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = 'clinical' AND c.relname = :table
                        """
                    ),
                    {"table": table},
                ).scalar_one()
                assert rls_enabled is True, f"{table}: RLS not forced"

                policy_count = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM pg_policies
                        WHERE schemaname = 'clinical' AND tablename = :table
                        """
                    ),
                    {"table": table},
                ).scalar_one()
                assert policy_count == 4, f"{table}: expected 4 policies, got {policy_count}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_appointment_composite_foreign_keys() -> None:
    """Appointments must reference patients, doctors, and locations via composite FKs."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    fk_checks = (
        ("fk_appointments_patient", "patients", "core"),
        ("fk_appointments_doctor", "doctors", "core"),
        ("fk_appointments_location", "tenant_locations", "platform"),
    )

    try:
        with engine.connect() as conn:
            for constraint, ref_table, ref_schema in fk_checks:
                defn = conn.execute(
                    text(
                        """
                        SELECT pg_get_constraintdef(c.oid)
                        FROM pg_constraint c
                        JOIN pg_class t ON t.oid = c.conrelid
                        JOIN pg_namespace n ON n.oid = t.relnamespace
                        WHERE n.nspname = 'clinical'
                          AND t.relname = 'appointments'
                          AND c.conname = :constraint
                        """
                    ),
                    {"constraint": constraint},
                ).scalar_one()
                assert "FOREIGN KEY (tenant_id" in defn, defn
                assert f"REFERENCES {ref_schema}.{ref_table}(tenant_id, id)" in defn, defn
    finally:
        engine.dispose()


@pytest.mark.integration
def test_rls_hides_appointments_from_other_tenant() -> None:
    """Tenant B must not see Tenant A appointment rows under RLS."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    appointment_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"appt-a-{suffix_a}",
            email=f"appt-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"appt-b-{suffix_b}",
            email=f"appt-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        doctor_id = _provision_doctor(db, data_a["tenant_id"])
        _insert_patient(
            db,
            tenant_id=data_a["tenant_id"],
            patient_id=patient_id,
            mrn=f"MRN-2026-{suffix_a[:5].upper()}",
        )
        _insert_appointment(
            db,
            tenant_id=data_a["tenant_id"],
            appointment_id=appointment_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM clinical.appointments WHERE id = :id"),
            {"id": appointment_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_active_doctor_slot_unique_index_prevents_double_book() -> None:
    """Partial unique index blocks two active appointments on the same doctor slot."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    patient_a = uuid.uuid4()
    patient_b = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"appt-dup-{suffix}",
            email=f"appt-dup-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        doctor_id = _provision_doctor(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_a,
            mrn=f"MRN-2026-{suffix[:5].upper()}",
        )
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_b,
            mrn=f"MRN-2026-{suffix[3:8].upper()}",
        )
        _insert_appointment(
            db,
            tenant_id=tenant_id,
            appointment_id=uuid.uuid4(),
            patient_id=patient_a,
            doctor_id=doctor_id,
            start_time=time(10, 0),
            end_time=time(10, 20),
        )
        db.flush()

        with pytest.raises(Exception, match="uq_appointments_doctor_slot_active|duplicate key"):
            _insert_appointment(
                db,
                tenant_id=tenant_id,
                appointment_id=uuid.uuid4(),
                patient_id=patient_b,
                doctor_id=doctor_id,
                start_time=time(10, 0),
                end_time=time(10, 20),
            )
            db.flush()


@pytest.mark.integration
def test_cancelled_appointment_allows_slot_reuse() -> None:
    """Cancelled appointments do not block the same doctor slot (partial unique index)."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    patient_a = uuid.uuid4()
    patient_b = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"appt-reuse-{suffix}",
            email=f"appt-reuse-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        doctor_id = _provision_doctor(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_a,
            mrn=f"MRN-2026-{suffix[:5].upper()}",
        )
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_b,
            mrn=f"MRN-2026-{suffix[3:8].upper()}",
        )
        _insert_appointment(
            db,
            tenant_id=tenant_id,
            appointment_id=uuid.uuid4(),
            patient_id=patient_a,
            doctor_id=doctor_id,
            start_time=time(11, 0),
            end_time=time(11, 20),
            status="cancelled",
        )
        _insert_appointment(
            db,
            tenant_id=tenant_id,
            appointment_id=uuid.uuid4(),
            patient_id=patient_b,
            doctor_id=doctor_id,
            start_time=time(11, 0),
            end_time=time(11, 20),
            status="scheduled",
        )
        db.commit()

        count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM clinical.appointments
                WHERE tenant_id = :tenant_id
                  AND doctor_id = :doctor_id
                  AND start_time = :start_time
                  AND status = 'scheduled'
                  AND deleted_at IS NULL
                """
            ),
            {"tenant_id": tenant_id, "doctor_id": doctor_id, "start_time": time(11, 0)},
        ).scalar_one()
        assert count == 1
