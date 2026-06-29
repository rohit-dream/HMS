"""Integration tests — MVP-070 pg_trgm extension + patient search indexes."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_INDEXES = (
    "idx_patients_tenant_phone",
    "idx_patients_name_search",
    "idx_patients_name_trgm",
    "idx_patients_phone_trgm",
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
    first_name: str,
    last_name: str | None,
    phone: str,
    mrn: str,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO core.patients (
                id, tenant_id, mrn, first_name, last_name,
                date_of_birth, gender, phone
            ) VALUES (
                :id, :tenant_id, :mrn, :first_name, :last_name,
                :dob, 'female', :phone
            )
            """
        ),
        {
            "id": patient_id,
            "tenant_id": tenant_id,
            "mrn": mrn,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "dob": date(1990, 5, 15),
        },
    )


@pytest.mark.integration
def test_pg_trgm_extension_installed() -> None:
    """Migration 021 must enable the pg_trgm extension."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            installed = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
            ).scalar_one()
            assert installed is True
    finally:
        engine.dispose()


@pytest.mark.integration
def test_patient_search_indexes_exist() -> None:
    """All four search indexes must exist on core.patients."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for index_name in EXPECTED_INDEXES:
                exists = conn.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE schemaname = 'core'
                              AND tablename = 'patients'
                              AND indexname = :index_name
                        )
                        """
                    ),
                    {"index_name": index_name},
                ).scalar_one()
                assert exists is True, f"missing index {index_name}"

            trgm_methods = conn.execute(
                text(
                    """
                    SELECT am.amname
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_am am ON am.oid = c.relam
                    WHERE n.nspname = 'core'
                      AND c.relname IN ('idx_patients_name_trgm', 'idx_patients_phone_trgm')
                    """
                )
            ).fetchall()
            assert len(trgm_methods) == 2
            assert all(row[0] == "gin" for row in trgm_methods)
    finally:
        engine.dispose()


@pytest.mark.integration
def test_name_trgm_search_finds_partial_match() -> None:
    """pg_trgm index supports fuzzy name search within a tenant."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    patient_id = uuid.uuid4()

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"pat-search-{suffix}",
            email=f"pat-search-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            first_name="Anita",
            last_name="Sharma",
            phone="9876543210",
            mrn="MRN-2026-01001",
        )
        db.commit()

        set_rls_tenant_context(db, tenant_id)
        rows = db.execute(
            text(
                """
                SELECT id
                FROM core.patients
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                  AND (first_name || ' ' || COALESCE(last_name, '')) % :query
                """
            ),
            {"tenant_id": tenant_id, "query": "Anit Sharm"},
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == patient_id


@pytest.mark.integration
def test_phone_btree_lookup_by_tenant() -> None:
    """B-tree (tenant_id, phone) index supports exact phone lookup."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    patient_id = uuid.uuid4()
    phone = "9123456789"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"pat-phone-{suffix}",
            email=f"pat-phone-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            first_name="Ravi",
            last_name="Kumar",
            phone=phone,
            mrn="MRN-2026-01002",
        )
        db.commit()

        set_rls_tenant_context(db, tenant_id)
        found_id = db.execute(
            text(
                """
                SELECT id
                FROM core.patients
                WHERE tenant_id = :tenant_id
                  AND phone = :phone
                  AND deleted_at IS NULL
                """
            ),
            {"tenant_id": tenant_id, "phone": phone},
        ).scalar_one()
        assert found_id == patient_id


@pytest.mark.integration
def test_mrn_lookup_uses_unique_index() -> None:
    """MRN search uses uq_patients_tenant_mrn from migration 020."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    patient_id = uuid.uuid4()
    mrn = "MRN-2026-01003"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"pat-mrn-{suffix}",
            email=f"pat-mrn-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)
        _insert_patient(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            first_name="Priya",
            last_name="Singh",
            phone="9988776655",
            mrn=mrn,
        )
        db.commit()

        set_rls_tenant_context(db, tenant_id)
        found_id = db.execute(
            text(
                """
                SELECT id
                FROM core.patients
                WHERE tenant_id = :tenant_id AND mrn = :mrn
                """
            ),
            {"tenant_id": tenant_id, "mrn": mrn},
        ).scalar_one()
        assert found_id == patient_id

        index_exists = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'core'
                      AND tablename = 'patients'
                      AND indexname = 'uq_patients_tenant_mrn'
                )
                """
            )
        ).scalar_one()
        assert index_exists is True
