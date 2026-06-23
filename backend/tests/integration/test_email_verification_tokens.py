"""Integration tests — MVP-022 email_verification_tokens table."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CORE_AUTH_RLS_TABLES
from app.domains.identity.constants import EMAIL_VERIFICATION_TOKEN_HOURS
from app.domains.identity.repositories.email_verification_repository import EmailVerificationRepository
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
def test_email_verification_tokens_table_exists() -> None:
    """Migration 013 must create core.email_verification_tokens with expected columns."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'core' AND table_name = 'email_verification_tokens'
                    """
                )
            ).first()
            assert exists is not None

            columns = {
                row.column_name
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'core'
                          AND table_name = 'email_verification_tokens'
                        """
                    )
                )
            }
            for col in ("tenant_id", "user_id", "token_hash", "expires_at", "used_at"):
                assert col in columns
    finally:
        engine.dispose()


@pytest.mark.integration
def test_email_verification_tokens_have_rls() -> None:
    """email_verification_tokens must have FORCE RLS and four policies."""
    _run_alembic_upgrade()
    assert "email_verification_tokens" in CORE_AUTH_RLS_TABLES

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
                    WHERE n.nspname = 'core' AND c.relname = 'email_verification_tokens'
                    """
                )
            ).one()
            assert row[0] is True
            assert row[1] is True

            policy_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*) FROM pg_policies
                    WHERE schemaname = 'core' AND tablename = 'email_verification_tokens'
                    """
                )
            ).scalar_one()
            assert policy_count == 4
    finally:
        engine.dispose()


@pytest.mark.integration
def test_email_verification_repository_create_and_lookup() -> None:
    """Repository must create and retrieve valid tokens within tenant scope."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"verify-{suffix}",
            email=f"verify-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        db.commit()

        use_rls_enforced_role(db)
        repo = EmailVerificationRepository(db, data["tenant_id"])
        expires = datetime.now(UTC) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_HOURS)
        token = repo.create_token(
            user_id=data["user_id"],
            token_hash="verify-hash-abc",
            expires_at=expires,
        )
        db.commit()
        repo.apply_rls_context()

        found = repo.get_valid_by_hash("verify-hash-abc")
        assert found is not None
        assert found.id == token.id
        assert found.user_id == data["user_id"]


@pytest.mark.integration
def test_email_verification_tokens_hidden_from_other_tenant() -> None:
    """Tenant B must not read Tenant A verification tokens."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    token_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"ev-a-{suffix_a}",
            email=f"ev-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"ev-b-{suffix_b}",
            email=f"ev-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        db.execute(
            text(
                """
                INSERT INTO core.email_verification_tokens (
                    id, tenant_id, user_id, token_hash, expires_at
                ) VALUES (
                    :id, :tenant_id, :user_id, :token_hash,
                    NOW() + interval '24 hours'
                )
                """
            ),
            {
                "id": token_id,
                "tenant_id": data_a["tenant_id"],
                "user_id": data_a["user_id"],
                "token_hash": "ev-token-hash-a",
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.email_verification_tokens WHERE id = :id"),
            {"id": token_id},
        ).scalar_one()
        assert count == 0

        repo_b = EmailVerificationRepository(db, data_b["tenant_id"])
        assert repo_b.get_valid_by_hash("ev-token-hash-a") is None
