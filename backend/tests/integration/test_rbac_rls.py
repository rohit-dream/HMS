"""Integration tests — MVP-036 RBAC + user_invite_tokens RLS."""

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
from app.db.rls_policies import CORE_RBAC_INVITE_RLS_TABLES
from app.domains.identity.repositories.rbac_repository import RbacRepository
from app.domains.identity.repositories.user_invite_repository import UserInviteRepository
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
def test_rbac_and_invite_tables_have_rls_enabled() -> None:
    """RBAC tables and user_invite_tokens must have FORCE RLS with four policies."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in CORE_RBAC_INVITE_RLS_TABLES:
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
def test_user_invite_tokens_table_exists() -> None:
    """Migration 015 must create core.user_invite_tokens with expected columns."""
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
                        WHERE table_schema = 'core' AND table_name = 'user_invite_tokens'
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
                        WHERE table_schema = 'core' AND table_name = 'user_invite_tokens'
                        """
                    )
                )
            }
            for col in (
                "id",
                "tenant_id",
                "user_id",
                "token_hash",
                "expires_at",
                "used_at",
                "created_at",
            ):
                assert col in columns, f"missing column {col}"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_rls_hides_roles_from_other_tenant() -> None:
    """Tenant B must not see Tenant A roles via direct SQL under RLS."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"rbac-a-{suffix_a}",
            email=f"rbac-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"rbac-b-{suffix_b}",
            email=f"rbac-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_a["tenant_id"])
        role_a = RbacRepository(db).get_role_by_code(data_a["tenant_id"], "hospital_admin")
        assert role_a is not None

        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.roles WHERE id = :id"),
            {"id": role_a.id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_rls_hides_user_roles_from_other_tenant() -> None:
    """Tenant B must not see Tenant A user_roles assignments."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"ur-a-{suffix_a}",
            email=f"ur-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"ur-b-{suffix_b}",
            email=f"ur-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_a["tenant_id"])
        assignment_id = db.execute(
            text(
                """
                SELECT id FROM core.user_roles
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                LIMIT 1
                """
            ),
            {"tenant_id": data_a["tenant_id"], "user_id": data_a["user_id"]},
        ).scalar_one()

        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.user_roles WHERE id = :id"),
            {"id": assignment_id},
        ).scalar_one()
        assert count == 0


@pytest.mark.integration
def test_user_invite_tokens_hidden_from_other_tenant() -> None:
    """Tenant B must not read Tenant A invite tokens."""
    _run_alembic_upgrade()
    suffix_a = uuid.uuid4().hex[:8]
    suffix_b = uuid.uuid4().hex[:8]
    token_id = uuid.uuid4()

    with session_scope() as db:
        data_a = provision_tenant_with_role(
            db,
            slug=f"inv-a-{suffix_a}",
            email=f"inv-a-{suffix_a}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        data_b = provision_tenant_with_role(
            db,
            slug=f"inv-b-{suffix_b}",
            email=f"inv-b-{suffix_b}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )

        set_rls_tenant_context(db, data_a["tenant_id"])
        db.execute(
            text(
                """
                INSERT INTO core.user_invite_tokens (
                    id, tenant_id, user_id, token_hash, expires_at
                ) VALUES (
                    :id, :tenant_id, :user_id, :token_hash,
                    NOW() + interval '72 hours'
                )
                """
            ),
            {
                "id": token_id,
                "tenant_id": data_a["tenant_id"],
                "user_id": data_a["user_id"],
                "token_hash": "invite-token-hash-a",
            },
        )
        db.commit()

        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data_b["tenant_id"])
        count = db.execute(
            text("SELECT COUNT(*) FROM core.user_invite_tokens WHERE id = :id"),
            {"id": token_id},
        ).scalar_one()
        assert count == 0

        repo_b = UserInviteRepository(db, data_b["tenant_id"])
        assert repo_b.get_valid_by_hash("invite-token-hash-a") is None


@pytest.mark.integration
def test_user_invite_repository_create_and_lookup() -> None:
    """Tenant-scoped invite repository can create and fetch valid tokens."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"inv-repo-{suffix}",
            email=f"inv-repo-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
        )
        repo = UserInviteRepository(db, data["tenant_id"])
        expires = datetime.now(UTC) + timedelta(hours=72)
        token = repo.create_token(
            user_id=data["user_id"],
            token_hash="invite-repo-hash",
            expires_at=expires,
            created_by=data["user_id"],
        )
        db.commit()
        repo.apply_rls_context()

        found = repo.get_valid_by_hash("invite-repo-hash")
        assert found is not None
        assert found.id == token.id
        assert found.user_id == data["user_id"]
