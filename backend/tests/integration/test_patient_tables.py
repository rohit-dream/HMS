"""Integration tests — MVP-069 patient tables + RLS."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CORE_PATIENT_RLS_TABLES
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]

PATIENT_TABLES = ("patients", "patient_allergies", "patient_contacts", "patient_documents")


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
    mrn: str = "MRN-2026-00001",
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


@pytest.mark.integration
def test_patient_tables_exist_with_expected_columns() -> None:
    """Migration 020 must create all four core patient tables."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in PATIENT_TABLES:
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

            patient_cols = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'core' AND table_name = 'patients'
                        """
                    )
                )
            }
            for col in (
                "tenant_id",
                "mrn",
                "first_name",
                "last_name",
                "date_of_birth",
                "gender",
                "phone",
                "consent_given_at",
                "consent_method",
                "chronic_conditions",
                "location_id",
            ):
                assert col in patient_cols, f"patients missing column {col}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_patient_tables_have_force_rls_with_four_policies() -> None:
    """Patient tables must have FORCE RLS with standard tenant isolation policies."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in CORE_PATIENT_RLS_TABLES:
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
def test_patient_tables_use_composite_foreign_keys() -> None:
    """Child patient tables must reference patients via composite (tenant_id, id) FKs."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    composite_fk_checks = (
        ("patient_allergies", "fk_patient_allergies_patient", "patients"),
        ("patient_contacts", "fk_patient_contacts_patient", "patients"),
        ("patient_documents", "fk_patient_documents_patient", "patients"),
        ("patients", "fk_patients_location", "tenant_locations"),
    )

    try:
        with engine.connect() as conn:
            for table, constraint, ref_table in composite_fk_checks:
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
                assert "FOREIGN KEY (tenant_id" in defn, defn
                if ref_table == "tenant_locations":
                    assert f"REFERENCES platform.{ref_table}(tenant_id, id)" in defn, defn
                else:
                    assert f"REFERENCES core.{ref_table}(tenant_id, id)" in defn, defn
    finally:
        engine.dispose()


@pytest.mark.integration
def test_rls_hides_patients_from_other_tenant() -> None:
    """Tenant B must not see Tenant A patient rows under RLS."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"pat-a-{suffix_a}",
            email=f"pat-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"pat-b-{suffix_b}",
            email=f"pat-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        _insert_patient(db, tenant_id=data_a["tenant_id"], patient_id=patient_id)
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.patients WHERE id = :id"),
            {"id": patient_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_rls_hides_patient_child_rows_from_other_tenant() -> None:
    """Tenant B must not see Tenant A allergy, contact, or document rows."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    patient_id = uuid.uuid4()
    allergy_id = uuid.uuid4()
    contact_id = uuid.uuid4()
    document_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"pat-child-a-{suffix_a}",
            email=f"pat-child-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"pat-child-b-{suffix_b}",
            email=f"pat-child-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        _insert_patient(db, tenant_id=data_a["tenant_id"], patient_id=patient_id)
        db.execute(
            text(
                """
                INSERT INTO core.patient_allergies (
                    id, tenant_id, patient_id, allergen, severity
                ) VALUES (
                    :id, :tenant_id, :patient_id, 'Penicillin', 'severe'
                )
                """
            ),
            {"id": allergy_id, "tenant_id": data_a["tenant_id"], "patient_id": patient_id},
        )
        db.execute(
            text(
                """
                INSERT INTO core.patient_contacts (
                    id, tenant_id, patient_id, name, relationship, phone
                ) VALUES (
                    :id, :tenant_id, :patient_id, 'Raj Sharma', 'spouse', '9876543211'
                )
                """
            ),
            {"id": contact_id, "tenant_id": data_a["tenant_id"], "patient_id": patient_id},
        )
        db.execute(
            text(
                """
                INSERT INTO core.patient_documents (
                    id, tenant_id, patient_id, document_type,
                    file_name, file_path, file_size_bytes, mime_type
                ) VALUES (
                    :id, :tenant_id, :patient_id, 'consent',
                    'consent.pdf', 'tenants/x/patients/y/consent.pdf', 1024, 'application/pdf'
                )
                """
            ),
            {"id": document_id, "tenant_id": data_a["tenant_id"], "patient_id": patient_id},
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        allergy_count = db.execute(
            text("SELECT COUNT(*) FROM core.patient_allergies WHERE id = :id"),
            {"id": allergy_id},
        ).scalar_one()
        contact_count = db.execute(
            text("SELECT COUNT(*) FROM core.patient_contacts WHERE id = :id"),
            {"id": contact_id},
        ).scalar_one()
        document_count = db.execute(
            text("SELECT COUNT(*) FROM core.patient_documents WHERE id = :id"),
            {"id": document_id},
        ).scalar_one()
        assert allergy_count == 0
        assert contact_count == 0
        assert document_count == 0


@pytest.mark.integration
def test_mrn_unique_per_tenant_not_globally() -> None:
    """Same MRN may exist in different tenants; duplicate within tenant is rejected."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    shared_mrn = "MRN-2026-00099"

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"pat-mrn-a-{suffix_a}",
            email=f"pat-mrn-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"pat-mrn-b-{suffix_b}",
            email=f"pat-mrn-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        _insert_patient(
            db,
            tenant_id=data_a["tenant_id"],
            patient_id=uuid.uuid4(),
            mrn=shared_mrn,
        )

        set_rls_tenant_context(db, data_b["tenant_id"])
        _insert_patient(
            db,
            tenant_id=data_b["tenant_id"],
            patient_id=uuid.uuid4(),
            mrn=shared_mrn,
        )
        db.commit()

        set_rls_tenant_context(db, data_a["tenant_id"])
        with pytest.raises(Exception):
            _insert_patient(
                db,
                tenant_id=data_a["tenant_id"],
                patient_id=uuid.uuid4(),
                mrn=shared_mrn,
            )
            db.commit()
