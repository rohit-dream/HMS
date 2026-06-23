"""Integration tests — MVP-021 core auth table RLS policies."""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.constants import TENANT_SLUG_HEADER
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.db.rls_policies import CORE_AUTH_RLS_TABLES
from app.domains.identity.repositories.session_repository import SessionRepository
from app.domains.identity.repositories.user_repository import UserRepository
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
def test_core_auth_tables_have_rls_enabled() -> None:
    """users, user_sessions, and password_reset_tokens must have FORCE RLS."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in CORE_AUTH_RLS_TABLES:
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
def test_rls_hides_users_from_other_tenant() -> None:
    """Tenant B context must not see Tenant A users via direct SQL."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"auth-a-{suffix_a}",
            email=f"user-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"auth-b-{suffix_b}",
            email=f"user-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.users WHERE id = :id"),
            {"id": data_a["user_id"]},
        ).scalar_one()
        assert count == 0

        set_rls_tenant_context(db, data_a["tenant_id"])
        visible = db.execute(
            text("SELECT COUNT(*) FROM core.users WHERE id = :id"),
            {"id": data_a["user_id"]},
        ).scalar_one()
        assert visible == 1


@pytest.mark.integration
def test_user_repository_respects_auth_rls() -> None:
    """UserRepository queries under hms_app must not return cross-tenant users."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"repo-a-{suffix_a}",
            email=f"repo-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"repo-b-{suffix_b}",
            email=f"repo-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        db.commit()

        use_rls_enforced_role(db)
        repo_b = UserRepository(db, data_b["tenant_id"])
        assert repo_b.get_by_id(data_a["user_id"]) is None
        assert repo_b.get_by_email(data_a["email"]) is None

        repo_a = UserRepository(db, data_a["tenant_id"])
        user = repo_a.get_by_id(data_a["user_id"])
        assert user is not None
        assert user.email == data_a["email"]


@pytest.mark.integration
def test_rls_hides_user_sessions_from_other_tenant() -> None:
    """Tenant B must not see Tenant A refresh token sessions."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"sess-a-{suffix_a}",
            email=f"sess-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"sess-b-{suffix_b}",
            email=f"sess-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        session_repo = SessionRepository(db, data_a["tenant_id"])
        session = session_repo.create_session(
            user_id=data_a["user_id"],
            refresh_token_hash="hash-tenant-a-session",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        db.commit()
        session_id = session.id

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.user_sessions WHERE id = :id"),
            {"id": session_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_rls_hides_password_reset_tokens_from_other_tenant() -> None:
    """Tenant B must not see Tenant A password reset tokens."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    token_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"reset-a-{suffix_a}",
            email=f"reset-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"reset-b-{suffix_b}",
            email=f"reset-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        db.execute(
            text(
                """
                INSERT INTO core.password_reset_tokens (
                    id, tenant_id, user_id, token_hash, expires_at
                ) VALUES (
                    :id, :tenant_id, :user_id, :token_hash, NOW() + interval '1 hour'
                )
                """
            ),
            {
                "id": token_id,
                "tenant_id": data_a["tenant_id"],
                "user_id": data_a["user_id"],
                "token_hash": "reset-token-hash-a",
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.password_reset_tokens WHERE id = :id"),
            {"id": token_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_auth_rls_missing_context_returns_no_rows() -> None:
    """Without app.tenant_id, auth table SELECT returns zero rows (fail-safe)."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            conn.execute(text("SET ROLE hms_app"))
            conn.execute(text("RESET app.tenant_id"))
            for table in CORE_AUTH_RLS_TABLES:
                count = conn.execute(text(f"SELECT COUNT(*) FROM core.{table}")).scalar_one()
                assert count == 0, f"{table} should return 0 rows without tenant context"
            conn.execute(text("RESET ROLE"))
    finally:
        engine.dispose()


@pytest.mark.integration
def test_login_works_with_core_auth_rls(client: TestClient) -> None:
    """Login flow must succeed when tenant context is bound before user lookup."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]
    slug = f"login-rls-{suffix}"
    email = f"login-rls-{suffix}@example.com"
    password = "SecurePass@123"

    with session_scope() as db:
        provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password(password),
            role_code="hospital_admin",
        )
        db.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={TENANT_SLUG_HEADER: slug},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "access_token" in resp.json()["data"]
