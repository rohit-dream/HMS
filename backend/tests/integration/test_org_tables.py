"""Integration tests — MVP-059 org tables + RLS."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CORE_ORG_RLS_TABLES
from app.domains.platform.repositories.location_repository import LocationRepository
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]

ORG_TABLES = ("departments", "staff", "doctors", "doctor_schedules")


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _primary_location_id(db, tenant_id: uuid.UUID) -> uuid.UUID:
    location = LocationRepository(db, tenant_id).get_primary()
    assert location is not None
    return location.id


@pytest.mark.integration
def test_org_tables_exist_with_expected_columns() -> None:
    """Migration 018 must create all four core org tables."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in ORG_TABLES:
                exists = conn.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_schema = 'core' AND table_name = :table
                        )
                        """
                    ),
                    {"table": table},
                ).scalar_one()
                assert exists is True, f"missing table core.{table}"

            dept_cols = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'core' AND table_name = 'departments'
                        """
                    )
                )
            }
            for col in ("tenant_id", "name", "code", "head_staff_id", "location_id", "is_active"):
                assert col in dept_cols, f"departments missing column {col}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_org_tables_have_force_rls_with_four_policies() -> None:
    """Org tables must have FORCE RLS with standard tenant isolation policies."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in CORE_ORG_RLS_TABLES:
                row = conn.execute(
                    text(
                        """
                        SELECT c.relrowsecurity, c.relforcerowsecurity
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = 'core' AND c.relname = :table
                        """
                    ),
                    {"table": table},
                ).one()
                assert row[0] is True, f"{table}: RLS not enabled"
                assert row[1] is True, f"{table}: FORCE RLS not enabled"

                policy_count = conn.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM pg_policies
                        WHERE schemaname = 'core' AND tablename = :table
                        """
                    ),
                    {"table": table},
                ).scalar_one()
                assert policy_count == 4, f"{table}: expected 4 policies, got {policy_count}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_org_tables_use_composite_foreign_keys() -> None:
    """Cross-table org FKs must use composite (tenant_id, id) references."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    composite_fk_checks = (
        ("staff", "fk_staff_department", ("tenant_id", "department_id"), "departments"),
        ("doctors", "fk_doctors_staff", ("tenant_id", "staff_id"), "staff"),
        (
            "doctor_schedules",
            "fk_doctor_schedules_doctor",
            ("tenant_id", "doctor_id"),
            "doctors",
        ),
        (
            "departments",
            "fk_departments_head_staff",
            ("tenant_id", "head_staff_id"),
            "staff",
        ),
    )

    try:
        with engine.connect() as conn:
            for table, constraint, src_cols, ref_table in composite_fk_checks:
                defn = conn.execute(
                    text(
                        """
                        SELECT pg_get_constraintdef(c.oid)
                        FROM pg_constraint c
                        JOIN pg_class t ON t.oid = c.conrelid
                        JOIN pg_namespace n ON n.oid = t.relnamespace
                        WHERE n.nspname = 'core'
                          AND t.relname = :table
                          AND c.conname = :constraint
                        """
                    ),
                    {"table": table, "constraint": constraint},
                ).scalar_one()
                src_sql = ", ".join(src_cols)
                assert f"FOREIGN KEY ({src_sql})" in defn, defn
                assert f"REFERENCES core.{ref_table}(tenant_id, id)" in defn, defn
    finally:
        engine.dispose()


@pytest.mark.integration
def test_rls_hides_departments_from_other_tenant() -> None:
    """Tenant B must not see Tenant A departments under RLS."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    dept_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"org-a-{suffix_a}",
            email=f"org-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"org-b-{suffix_b}",
            email=f"org-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        location_id = _primary_location_id(db, data_a["tenant_id"])

        set_rls_tenant_context(db, data_a["tenant_id"])
        db.execute(
            text(
                """
                INSERT INTO core.departments (
                    id, tenant_id, name, code, location_id, is_active
                ) VALUES (
                    :id, :tenant_id, 'Cardiology', 'CARD', :location_id, TRUE
                )
                """
            ),
            {
                "id": dept_id,
                "tenant_id": data_a["tenant_id"],
                "location_id": location_id,
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.departments WHERE id = :id"),
            {"id": dept_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_rls_hides_staff_and_doctors_from_other_tenant() -> None:
    """Tenant B must not see Tenant A staff or doctor rows."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    staff_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"org-staff-a-{suffix_a}",
            email=f"org-staff-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"org-staff-b-{suffix_b}",
            email=f"org-staff-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        db.execute(
            text(
                """
                INSERT INTO core.staff (
                    id, tenant_id, employee_code, first_name, last_name,
                    joining_date, status
                ) VALUES (
                    :id, :tenant_id, 'EMP001', 'Jane', 'Doe',
                    :joining_date, 'active'
                )
                """
            ),
            {
                "id": staff_id,
                "tenant_id": data_a["tenant_id"],
                "joining_date": date.today(),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO core.doctors (
                    id, tenant_id, staff_id, specialization, consultation_fee
                ) VALUES (
                    :id, :tenant_id, :staff_id, 'General Medicine', :fee
                )
                """
            ),
            {
                "id": doctor_id,
                "tenant_id": data_a["tenant_id"],
                "staff_id": staff_id,
                "fee": Decimal("500.00"),
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        staff_count = db.execute(
            text("SELECT COUNT(*) FROM core.staff WHERE id = :id"),
            {"id": staff_id},
        ).scalar_one()
        doctor_count = db.execute(
            text("SELECT COUNT(*) FROM core.doctors WHERE id = :id"),
            {"id": doctor_id},
        ).scalar_one()
        assert staff_count == 0
        assert doctor_count == 0


@pytest.mark.integration
def test_rls_hides_doctor_schedules_from_other_tenant() -> None:
    """Tenant B must not see Tenant A doctor schedule rows."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    staff_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    schedule_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"org-sch-a-{suffix_a}",
            email=f"org-sch-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"org-sch-b-{suffix_b}",
            email=f"org-sch-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        db.execute(
            text(
                """
                INSERT INTO core.staff (
                    id, tenant_id, employee_code, first_name, last_name,
                    joining_date, status
                ) VALUES (
                    :id, :tenant_id, 'EMP002', 'John', 'Smith',
                    :joining_date, 'active'
                )
                """
            ),
            {
                "id": staff_id,
                "tenant_id": data_a["tenant_id"],
                "joining_date": date.today(),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO core.doctors (
                    id, tenant_id, staff_id, specialization, consultation_fee
                ) VALUES (
                    :id, :tenant_id, :staff_id, 'Pediatrics', :fee
                )
                """
            ),
            {
                "id": doctor_id,
                "tenant_id": data_a["tenant_id"],
                "staff_id": staff_id,
                "fee": Decimal("750.00"),
            },
        )
        db.execute(
            text(
                """
                INSERT INTO core.doctor_schedules (
                    id, tenant_id, doctor_id, day_of_week,
                    start_time, end_time, slot_duration_minutes
                ) VALUES (
                    :id, :tenant_id, :doctor_id, 1,
                    '09:00', '12:00', 15
                )
                """
            ),
            {
                "id": schedule_id,
                "tenant_id": data_a["tenant_id"],
                "doctor_id": doctor_id,
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.doctor_schedules WHERE id = :id"),
            {"id": schedule_id},
        ).scalar_one()
        assert count == 0
