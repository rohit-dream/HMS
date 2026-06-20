"""RBAC provisioning — seed and clone roles/permissions per tenant."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import SYSTEM_TENANT_ID
from app.core.rbac.catalog import (
    PERMISSION_CATALOG,
    ROLE_CATALOG,
    ROLE_PERMISSION_MAP,
    TENANT_ROLE_CODES,
)
from app.domains.identity.repositories.rbac_repository import RbacRepository
from app.models.core.permission import Permission
from app.models.core.role import Role
from app.models.core.role_permission import RolePermission
from app.models.platform.tenant import Tenant


class RbacProvisioner:
    """Seed system tenant RBAC and clone templates to hospital tenants."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._repo = RbacRepository(db)

    def ensure_system_tenant(self) -> uuid.UUID:
        system_id = uuid.UUID(SYSTEM_TENANT_ID)
        tenant = self.db.get(Tenant, system_id)
        if tenant is None:
            tenant = Tenant(
                id=system_id,
                tenant_id=system_id,
                name="HMS Platform System",
                slug="system",
                subdomain="system",
                status="active",
                email="system@platform.com",
            )
            self.db.add(tenant)
            self.db.flush()
        return system_id

    def seed_system_rbac(self) -> None:
        """Create full permission catalog and all roles on system tenant."""
        tenant_id = self.ensure_system_tenant()
        self._seed_permissions(tenant_id)
        self._seed_roles(tenant_id, role_codes={code for code, _, _ in ROLE_CATALOG})
        self._seed_role_permissions(tenant_id)
        self.db.flush()

    def provision_tenant_rbac(self, tenant_id: uuid.UUID) -> None:
        """Clone RBAC templates from system tenant (excludes platform_admin)."""
        system_id = self.ensure_system_tenant()
        if tenant_id == system_id:
            return
        self._clone_permissions(system_id, tenant_id)
        self._seed_roles(tenant_id, role_codes=set(TENANT_ROLE_CODES))
        self._clone_role_permissions(system_id, tenant_id)
        self.db.flush()

    def assign_role(self, tenant_id: uuid.UUID, user_id: uuid.UUID, role_code: str) -> None:
        role = self._repo.get_role_by_code(tenant_id, role_code)
        if role is None:
            raise ValueError(f"Role not found: {role_code}")
        self._repo.assign_role_to_user(tenant_id, user_id, role.id)

    def _seed_permissions(self, tenant_id: uuid.UUID) -> None:
        for code, name, module in PERMISSION_CATALOG:
            if self._repo.get_permission_by_code(tenant_id, code):
                continue
            self.db.add(
                Permission(
                    tenant_id=tenant_id,
                    code=code,
                    name=name,
                    module=module,
                )
            )

    def _seed_roles(self, tenant_id: uuid.UUID, role_codes: set[str]) -> None:
        for code, name, description in ROLE_CATALOG:
            if code not in role_codes:
                continue
            if self._repo.get_role_by_code(tenant_id, code):
                continue
            self.db.add(
                Role(
                    tenant_id=tenant_id,
                    code=code,
                    name=name,
                    description=description,
                    is_system=True,
                    is_active=True,
                )
            )
        self.db.flush()

    def _seed_role_permissions(self, tenant_id: uuid.UUID) -> None:
        for role_code, perm_codes in ROLE_PERMISSION_MAP.items():
            role = self._repo.get_role_by_code(tenant_id, role_code)
            if role is None:
                continue
            for perm_code in perm_codes:
                permission = self._repo.get_permission_by_code(tenant_id, perm_code)
                if permission is None:
                    continue
                exists = self.db.scalars(
                    select(RolePermission).where(
                        RolePermission.tenant_id == tenant_id,
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                        RolePermission.deleted_at.is_(None),
                    )
                ).first()
                if exists:
                    continue
                self.db.add(
                    RolePermission(
                        tenant_id=tenant_id,
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

    def _clone_permissions(self, source_tenant_id: uuid.UUID, target_tenant_id: uuid.UUID) -> None:
        for perm in self._repo.list_permissions(source_tenant_id):
            if self._repo.get_permission_by_code(target_tenant_id, perm.code):
                continue
            self.db.add(
                Permission(
                    tenant_id=target_tenant_id,
                    code=perm.code,
                    name=perm.name,
                    module=perm.module,
                    description=perm.description,
                )
            )
        self.db.flush()

    def _clone_role_permissions(self, source_tenant_id: uuid.UUID, target_tenant_id: uuid.UUID) -> None:
        for role_code in TENANT_ROLE_CODES:
            source_role = self._repo.get_role_by_code(source_tenant_id, role_code)
            target_role = self._repo.get_role_by_code(target_tenant_id, role_code)
            if source_role is None or target_role is None:
                continue
            perm_codes = ROLE_PERMISSION_MAP.get(role_code, frozenset())
            for perm_code in perm_codes:
                target_perm = self._repo.get_permission_by_code(target_tenant_id, perm_code)
                if target_perm is None:
                    continue
                exists = self.db.scalars(
                    select(RolePermission).where(
                        RolePermission.tenant_id == target_tenant_id,
                        RolePermission.role_id == target_role.id,
                        RolePermission.permission_id == target_perm.id,
                        RolePermission.deleted_at.is_(None),
                    )
                ).first()
                if exists:
                    continue
                self.db.add(
                    RolePermission(
                        tenant_id=target_tenant_id,
                        role_id=target_role.id,
                        permission_id=target_perm.id,
                    )
                )
