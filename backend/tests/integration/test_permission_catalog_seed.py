"""Integration tests — MVP-037 permission catalog seed in database."""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.constants import SYSTEM_TENANT_ID
from app.core.database import session_scope, set_rls_tenant_context
from app.core.permissions import PermissionResolver
from app.core.security import hash_password
from app.domains.identity.repositories.rbac_repository import RbacRepository
from app.models.core.permission import Permission
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
def test_system_tenant_has_sprint4_permissions() -> None:
    """System tenant catalog must include opd:queue and admin:staff after migration 016."""
    _run_alembic_upgrade()
    system_id = uuid.UUID(SYSTEM_TENANT_ID)

    with session_scope() as db:
        set_rls_tenant_context(db, system_id)
        repo = RbacRepository(db)
        assert repo.get_permission_by_code(system_id, "opd:queue") is not None
        assert repo.get_permission_by_code(system_id, "admin:staff") is not None


@pytest.mark.integration
def test_provisioned_tenant_has_sprint4_permissions_and_role_mappings() -> None:
    """New tenants receive seeded permissions and role grants from catalog."""
    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        admin_data = provision_tenant_with_role(
            db,
            slug=f"perm-admin-{suffix}",
            email=f"perm-admin-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        recv_data = provision_tenant_with_role(
            db,
            slug=f"perm-recv-{suffix}",
            email=f"perm-recv-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="receptionist",
        )

        repo = RbacRepository(db)
        tenant_id = admin_data["tenant_id"]
        set_rls_tenant_context(db, tenant_id)

        codes = {perm.code for perm in repo.list_permissions(tenant_id)}
        assert "opd:queue" in codes
        assert "admin:staff" in codes

        admin_perms = repo.get_user_permissions(tenant_id, admin_data["user_id"])
        recv_perms = repo.get_user_permissions(recv_data["tenant_id"], recv_data["user_id"])
        assert "admin:staff" in admin_perms
        assert "opd:queue" in admin_perms
        assert "opd:queue" in recv_perms
        assert "admin:staff" not in recv_perms

        resolver = PermissionResolver(db)
        assert "opd:queue" in resolver.get_permissions(
            recv_data["tenant_id"], recv_data["user_id"]
        )


@pytest.mark.integration
def test_permission_catalog_count_matches_code_definition() -> None:
    """Every catalog code exists once per tenant after sync."""
    from app.core.rbac.catalog import PERMISSION_CATALOG

    _run_alembic_upgrade()
    suffix = uuid.uuid4().hex[:8]

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=f"perm-count-{suffix}",
            email=f"perm-count-{suffix}@example.com",
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        set_rls_tenant_context(db, data["tenant_id"])
        rows = db.scalars(
            select(Permission).where(
                Permission.tenant_id == data["tenant_id"],
                Permission.deleted_at.is_(None),
            )
        ).all()
        assert len(rows) == len(PERMISSION_CATALOG)
