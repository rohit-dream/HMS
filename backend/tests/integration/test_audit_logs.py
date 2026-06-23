"""Integration tests — MVP-033 audit.audit_logs table."""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import AUDIT_RLS_TABLES
from tests.helpers.rbac import provision_tenant_with_role

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.integration
def test_audit_logs_table_exists() -> None:
    """Migration 014 must create audit.audit_logs with expected columns."""
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
                        WHERE table_schema = 'audit' AND table_name = 'audit_logs'
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
                        WHERE table_schema = 'audit' AND table_name = 'audit_logs'
                        """
                    )
                )
            }
            for col in (
                "id",
                "tenant_id",
                "user_id",
                "action",
                "entity_type",
                "entity_id",
                "ip_address",
                "user_agent",
                "request_id",
                "metadata",
                "created_at",
            ):
                assert col in columns, f"missing column {col}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_audit_logs_have_rls() -> None:
    """audit_logs must have FORCE RLS and four tenant isolation policies."""
    _run_alembic_upgrade()
    assert "audit_logs" in AUDIT_RLS_TABLES

    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'audit' AND c.relname = 'audit_logs'
                    """
                )
            ).one()
            assert row[0] is True
            assert row[1] is True

            policy_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM pg_policies
                    WHERE schemaname = 'audit' AND tablename = 'audit_logs'
                    """
                )
            ).scalar_one()
            assert policy_count == 4
    finally:
        engine.dispose()


@pytest.mark.integration
def test_audit_logs_hidden_from_other_tenant() -> None:
    """Tenant B cannot read tenant A audit rows under RLS."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    log_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"audit-a-{suffix_a}",
            email=f"audit-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"audit-b-{suffix_b}",
            email=f"audit-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        db.execute(
            text(
                """
                INSERT INTO audit.audit_logs (
                    id, tenant_id, action, entity_type
                ) VALUES (
                    :id, :tenant_id, 'login', 'auth'
                )
                """
            ),
            {"id": log_id, "tenant_id": data_a["tenant_id"]},
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM audit.audit_logs WHERE id = :id"),
            {"id": log_id},
        ).scalar_one()
        assert count == 0
