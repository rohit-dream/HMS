"""Integration tests — MVP-071 core.generate_mrn() function."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _current_year() -> int:
    return datetime.now().year


def _expected_mrn(seq: int, *, year: int | None = None) -> str:
    y = year if year is not None else _current_year()
    return f"MRN-{y}-{seq:05d}"


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _call_generate_mrn(db, tenant_id: uuid.UUID) -> str:
    return db.execute(
        text("SELECT core.generate_mrn(:tenant_id)"),
        {"tenant_id": tenant_id},
    ).scalar_one()


def _insert_patient_with_mrn(
    db,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    mrn: str,
    phone: str,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO core.patients (
                id, tenant_id, mrn, first_name, date_of_birth, gender, phone
            ) VALUES (
                :id, :tenant_id, :mrn, 'Test', :dob, 'male', :phone
            )
            """
        ),
        {
            "id": patient_id,
            "tenant_id": tenant_id,
            "mrn": mrn,
            "phone": phone,
            "dob": date(1990, 1, 1),
        },
    )


@pytest.mark.integration
def test_generate_mrn_function_exists() -> None:
    """Migration 022 must install core.generate_mrn(UUID)."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_proc p
                        JOIN pg_namespace n ON n.oid = p.pronamespace
                        WHERE n.nspname = 'core'
                          AND p.proname = 'generate_mrn'
                    )
                    """
                )
            ).scalar_one()
            assert exists is True
    finally:
        engine.dispose()


@pytest.mark.integration
def test_first_mrn_starts_at_one() -> None:
    """First MRN for a tenant in the current year is MRN-YYYY-00001."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"mrn-first-{suffix}",
            email=f"mrn-first-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)

        mrn = _call_generate_mrn(db, tenant_id)
        assert mrn == _expected_mrn(1)


@pytest.mark.integration
def test_generate_mrn_increments_sequentially() -> None:
    """Each call advances the sequence for the same tenant and year."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"mrn-seq-{suffix}",
            email=f"mrn-seq-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)

        _insert_patient_with_mrn(
            db,
            tenant_id=tenant_id,
            patient_id=uuid.uuid4(),
            mrn=_expected_mrn(1),
            phone="9000000001",
        )
        _insert_patient_with_mrn(
            db,
            tenant_id=tenant_id,
            patient_id=uuid.uuid4(),
            mrn=_expected_mrn(2),
            phone="9000000002",
        )
        db.commit()

        set_rls_tenant_context(db, tenant_id)
        next_mrn = _call_generate_mrn(db, tenant_id)
        assert next_mrn == _expected_mrn(3)


@pytest.mark.integration
def test_generate_mrn_independent_per_tenant() -> None:
    """Each tenant maintains its own MRN sequence."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"mrn-a-{suffix_a}",
            email=f"mrn-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"mrn-b-{suffix_b}",
            email=f"mrn-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        _insert_patient_with_mrn(
            db,
            tenant_id=data_a["tenant_id"],
            patient_id=uuid.uuid4(),
            mrn=_expected_mrn(1),
            phone="9111111111",
        )
        _insert_patient_with_mrn(
            db,
            tenant_id=data_a["tenant_id"],
            patient_id=uuid.uuid4(),
            mrn=_expected_mrn(2),
            phone="9111111112",
        )
        db.commit()

        set_rls_tenant_context(db, data_b["tenant_id"])
        mrn_b = _call_generate_mrn(db, data_b["tenant_id"])
        assert mrn_b == _expected_mrn(1)

        set_rls_tenant_context(db, data_a["tenant_id"])
        mrn_a = _call_generate_mrn(db, data_a["tenant_id"])
        assert mrn_a == _expected_mrn(3)


@pytest.mark.integration
def test_generate_mrn_skips_gaps_from_existing_records() -> None:
    """Generator uses MAX existing sequence, not COUNT — gaps are preserved."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"mrn-gap-{suffix}",
            email=f"mrn-gap-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        tenant_id = data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)

        _insert_patient_with_mrn(
            db,
            tenant_id=tenant_id,
            patient_id=uuid.uuid4(),
            mrn=_expected_mrn(5),
            phone="9222222222",
        )
        db.commit()

        set_rls_tenant_context(db, tenant_id)
        next_mrn = _call_generate_mrn(db, tenant_id)
        assert next_mrn == _expected_mrn(6)


@pytest.mark.integration
def test_generate_mrn_rejects_tenant_context_mismatch() -> None:
    """hms_app cannot generate MRNs for a different tenant than app.tenant_id."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"mrn-ctx-a-{suffix_a}",
            email=f"mrn-ctx-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"mrn-ctx-b-{suffix_b}",
            email=f"mrn-ctx-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_a["tenant_id"])
        with pytest.raises(Exception, match="tenant_id does not match session context"):
            _call_generate_mrn(db, data_b["tenant_id"])
            db.commit()
