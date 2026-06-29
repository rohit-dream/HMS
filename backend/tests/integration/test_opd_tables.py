"""Integration tests — MVP-091 clinical OPD tables + RLS."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CLINICAL_OPD_RLS_TABLES
from app.domains.org.repositories.department_repository import DepartmentRepository
from app.domains.org.repositories.doctor_repository import DoctorRepository
from app.domains.org.repositories.staff_repository import StaffRepository
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]

OPD_VISIT_COLUMNS = (
    "id",
    "tenant_id",
    "visit_number",
    "patient_id",
    "doctor_id",
    "appointment_id",
    "location_id",
    "visit_date",
    "visit_type",
    "status",
    "token_number",
    "chief_complaint",
    "started_at",
    "completed_at",
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


def _insert_opd_visit(
    db,
    *,
    tenant_id: uuid.UUID,
    visit_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    visit_number: str | None = None,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO clinical.opd_visits (
                id, tenant_id, visit_number, patient_id, doctor_id,
                visit_date, visit_type, status, token_number, chief_complaint
            ) VALUES (
                :id, :tenant_id,
                COALESCE(:visit_number, clinical.generate_visit_number(:tenant_id)),
                :patient_id, :doctor_id,
                :visit_date, 'walk_in', 'waiting', 1, 'Fever'
            )
            """
        ),
        {
            "id": visit_id,
            "tenant_id": tenant_id,
            "visit_number": visit_number,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "visit_date": date.today(),
        },
    )


@pytest.mark.integration
def test_opd_tables_exist_with_expected_columns() -> None:
    """Migration 026 must create all seven OPD tables."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    expected_tables = CLINICAL_OPD_RLS_TABLES

    try:
        with engine.connect() as conn:
            for table in expected_tables:
                exists = conn.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_schema = 'clinical' AND table_name = :table
                        )
                        """
                    ),
                    {"table": table},
                ).scalar_one()
                assert exists is True, f"Missing table clinical.{table}"

            columns = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'clinical' AND table_name = 'opd_visits'
                        """
                    )
                )
            }
            for column in OPD_VISIT_COLUMNS:
                assert column in columns, f"Missing column: {column}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_opd_tables_rls_enabled_with_policies() -> None:
    """All OPD tables must have FORCE RLS and four tenant isolation policies."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in CLINICAL_OPD_RLS_TABLES:
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
def test_opd_visits_composite_foreign_keys() -> None:
    """OPD visits must reference patients, doctors, and appointments via composite FKs."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    fk_checks = (
        ("fk_opd_visits_patient", "patients", "core"),
        ("fk_opd_visits_doctor", "doctors", "core"),
        ("fk_opd_visits_appointment", "appointments", "clinical"),
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
                          AND t.relname = 'opd_visits'
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
def test_rls_hides_opd_visits_from_other_tenant() -> None:
    """Tenant B must not see Tenant A OPD visit rows under RLS."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    visit_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"opd-a-{suffix_a}",
            email=f"opd-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"opd-b-{suffix_b}",
            email=f"opd-b-{suffix_b}@example.com",
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
        _insert_opd_visit(
            db,
            tenant_id=data_a["tenant_id"],
            visit_id=visit_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM clinical.opd_visits WHERE id = :id"),
            {"id": visit_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_rls_hides_opd_child_rows_from_other_tenant() -> None:
    """Tenant B must not see Tenant A queue, vitals, notes, or prescription rows."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    visit_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    queue_id = uuid.uuid4()
    vitals_id = uuid.uuid4()
    note_id = uuid.uuid4()
    rx_id = uuid.uuid4()
    rx_item_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"opd-child-a-{suffix_a}",
            email=f"opd-child-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"opd-child-b-{suffix_b}",
            email=f"opd-child-b-{suffix_b}@example.com",
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
        _insert_opd_visit(
            db,
            tenant_id=data_a["tenant_id"],
            visit_id=visit_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_queue (
                    id, tenant_id, opd_visit_id, doctor_id, token_number, queue_date
                ) VALUES (
                    :id, :tenant_id, :visit_id, :doctor_id, 1, :queue_date
                )
                """
            ),
            {
                "id": queue_id,
                "tenant_id": data_a["tenant_id"],
                "visit_id": visit_id,
                "doctor_id": doctor_id,
                "queue_date": date.today(),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_vitals (
                    id, tenant_id, opd_visit_id, recorded_at, pulse_rate
                ) VALUES (
                    :id, :tenant_id, :visit_id, :recorded_at, 72
                )
                """
            ),
            {
                "id": vitals_id,
                "tenant_id": data_a["tenant_id"],
                "visit_id": visit_id,
                "recorded_at": datetime.now(timezone.utc),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_clinical_notes (
                    id, tenant_id, opd_visit_id, note_type, content
                ) VALUES (
                    :id, :tenant_id, :visit_id, 'general', 'Test note'
                )
                """
            ),
            {"id": note_id, "tenant_id": data_a["tenant_id"], "visit_id": visit_id},
        )
        rx_number = db.execute(
            text("SELECT clinical.generate_prescription_number(:tenant_id)"),
            {"tenant_id": data_a["tenant_id"]},
        ).scalar_one()
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_prescriptions (
                    id, tenant_id, opd_visit_id, patient_id, doctor_id,
                    prescription_number, prescribed_at
                ) VALUES (
                    :id, :tenant_id, :visit_id, :patient_id, :doctor_id,
                    :rx_number, :prescribed_at
                )
                """
            ),
            {
                "id": rx_id,
                "tenant_id": data_a["tenant_id"],
                "visit_id": visit_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "rx_number": rx_number,
                "prescribed_at": datetime.now(timezone.utc),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_prescription_items (
                    id, tenant_id, prescription_id, medicine_name,
                    dosage, frequency, duration
                ) VALUES (
                    :id, :tenant_id, :prescription_id, 'Paracetamol',
                    '500mg', 'twice daily', '5 days'
                )
                """
            ),
            {
                "id": rx_item_id,
                "tenant_id": data_a["tenant_id"],
                "prescription_id": rx_id,
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        for table, row_id in (
            ("opd_queue", queue_id),
            ("opd_vitals", vitals_id),
            ("opd_clinical_notes", note_id),
            ("opd_prescriptions", rx_id),
            ("opd_prescription_items", rx_item_id),
        ):
            count = db.execute(
                text(f"SELECT COUNT(*) FROM clinical.{table} WHERE id = :id"),
                {"id": row_id},
            ).scalar_one()
            assert count == 0, f"{table} row visible across tenants"


@pytest.mark.integration
def test_generate_visit_number_is_per_tenant_sequential() -> None:
    """clinical.generate_visit_number() returns OPD-YYYY-NNNNN per tenant."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"opd-num-{suffix}",
            email=f"opd-num-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        doctor_id = _provision_doctor(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            mrn=f"MRN-2026-{suffix[:5].upper()}",
        )

        first = db.execute(
            text("SELECT clinical.generate_visit_number(:tenant_id)"),
            {"tenant_id": tenant_id},
        ).scalar_one()
        _insert_opd_visit(
            db,
            tenant_id=tenant_id,
            visit_id=uuid.uuid4(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            visit_number=first,
        )
        second = db.execute(
            text("SELECT clinical.generate_visit_number(:tenant_id)"),
            {"tenant_id": tenant_id},
        ).scalar_one()
        db.commit()

        year = date.today().year
        assert first == f"OPD-{year}-00001"
        assert second == f"OPD-{year}-00002"


@pytest.mark.integration
def test_generate_prescription_number_is_per_tenant_sequential() -> None:
    """clinical.generate_prescription_number() returns RX-YYYY-NNNNN per tenant."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    visit_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"opd-rx-num-{suffix}",
            email=f"opd-rx-num-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        doctor_id = _provision_doctor(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            mrn=f"MRN-2026-{suffix[:5].upper()}",
        )
        _insert_opd_visit(
            db,
            tenant_id=tenant_id,
            visit_id=visit_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        )

        first = db.execute(
            text("SELECT clinical.generate_prescription_number(:tenant_id)"),
            {"tenant_id": tenant_id},
        ).scalar_one()
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_prescriptions (
                    id, tenant_id, opd_visit_id, patient_id, doctor_id,
                    prescription_number, prescribed_at
                ) VALUES (
                    :id, :tenant_id, :visit_id, :patient_id, :doctor_id,
                    :rx_number, :prescribed_at
                )
                """
            ),
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "visit_id": visit_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "rx_number": first,
                "prescribed_at": datetime.now(timezone.utc),
            },
        )
        second = db.execute(
            text("SELECT clinical.generate_prescription_number(:tenant_id)"),
            {"tenant_id": tenant_id},
        ).scalar_one()
        db.commit()

        year = date.today().year
        assert first == f"RX-{year}-00001"
        assert second == f"RX-{year}-00002"


@pytest.mark.integration
def test_opd_child_tables_cascade_on_visit_delete() -> None:
    """Queue, vitals, and notes rows cascade when parent visit is deleted."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    visit_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    queue_id = uuid.uuid4()
    vitals_id = uuid.uuid4()
    note_id = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"opd-cascade-{suffix}",
            email=f"opd-cascade-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        doctor_id = _provision_doctor(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            mrn=f"MRN-2026-{suffix[:5].upper()}",
        )
        _insert_opd_visit(
            db,
            tenant_id=tenant_id,
            visit_id=visit_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_queue (
                    id, tenant_id, opd_visit_id, doctor_id, token_number, queue_date
                ) VALUES (
                    :id, :tenant_id, :visit_id, :doctor_id, 1, :queue_date
                )
                """
            ),
            {
                "id": queue_id,
                "tenant_id": tenant_id,
                "visit_id": visit_id,
                "doctor_id": doctor_id,
                "queue_date": date.today(),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_vitals (
                    id, tenant_id, opd_visit_id, recorded_at, pulse_rate
                ) VALUES (
                    :id, :tenant_id, :visit_id, :recorded_at, 72
                )
                """
            ),
            {
                "id": vitals_id,
                "tenant_id": tenant_id,
                "visit_id": visit_id,
                "recorded_at": datetime.now(timezone.utc),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_clinical_notes (
                    id, tenant_id, opd_visit_id, note_type, content
                ) VALUES (
                    :id, :tenant_id, :visit_id, 'general', 'Test note'
                )
                """
            ),
            {"id": note_id, "tenant_id": tenant_id, "visit_id": visit_id},
        )
        db.flush()
        db.execute(
            text("DELETE FROM clinical.opd_visits WHERE id = :id AND tenant_id = :tenant_id"),
            {"id": visit_id, "tenant_id": tenant_id},
        )
        db.commit()

        for table, row_id in (
            ("opd_queue", queue_id),
            ("opd_vitals", vitals_id),
            ("opd_clinical_notes", note_id),
        ):
            count = db.execute(
                text(f"SELECT COUNT(*) FROM clinical.{table} WHERE id = :id"),
                {"id": row_id},
            ).scalar_one()
            assert count == 0, f"{table} row should cascade delete"


@pytest.mark.integration
def test_active_queue_visit_unique_index() -> None:
    """Only one active queue entry per visit is allowed."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    visit_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"opd-queue-{suffix}",
            email=f"opd-queue-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        doctor_id = _provision_doctor(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            mrn=f"MRN-2026-{suffix[:5].upper()}",
        )
        _insert_opd_visit(
            db,
            tenant_id=tenant_id,
            visit_id=visit_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
        )
        db.execute(
            text(
                """
                INSERT INTO clinical.opd_queue (
                    id, tenant_id, opd_visit_id, doctor_id, token_number, queue_date
                ) VALUES (
                    :id, :tenant_id, :visit_id, :doctor_id, 1, :queue_date
                )
                """
            ),
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "visit_id": visit_id,
                "doctor_id": doctor_id,
                "queue_date": date.today(),
            },
        )
        db.flush()

        with pytest.raises(Exception, match="uq_opd_queue_active_visit|duplicate key"):
            db.execute(
                text(
                    """
                    INSERT INTO clinical.opd_queue (
                        id, tenant_id, opd_visit_id, doctor_id, token_number, queue_date
                    ) VALUES (
                        :id, :tenant_id, :visit_id, :doctor_id, 2, :queue_date
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "tenant_id": tenant_id,
                    "visit_id": visit_id,
                    "doctor_id": doctor_id,
                    "queue_date": date.today(),
                },
            )
            db.flush()
