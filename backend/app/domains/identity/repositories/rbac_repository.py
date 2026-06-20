"""RBAC data access — roles, permissions, user role resolution."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core.permission import Permission
from app.models.core.role import Role
from app.models.core.role_permission import RolePermission
from app.models.core.user_role import UserRole
from app.repositories.base import TenantScopedRepository


class RbacRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_role_by_code(self, tenant_id: uuid.UUID, code: str) -> Role | None:
        stmt = select(Role).where(
            Role.tenant_id == tenant_id,
            Role.code == code,
            Role.deleted_at.is_(None),
            Role.is_active.is_(True),
        )
        return self.db.scalars(stmt).first()

    def get_permission_by_code(self, tenant_id: uuid.UUID, code: str) -> Permission | None:
        stmt = select(Permission).where(
            Permission.tenant_id == tenant_id,
            Permission.code == code,
            Permission.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first()

    def list_permissions(self, tenant_id: uuid.UUID) -> list[Permission]:
        stmt = select(Permission).where(
            Permission.tenant_id == tenant_id,
            Permission.deleted_at.is_(None),
        )
        return list(self.db.scalars(stmt).all())

    def list_roles(self, tenant_id: uuid.UUID) -> list[Role]:
        stmt = select(Role).where(
            Role.tenant_id == tenant_id,
            Role.deleted_at.is_(None),
            Role.is_active.is_(True),
        )
        return list(self.db.scalars(stmt).all())

    def get_user_role_codes(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> list[str]:
        stmt = (
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.tenant_id == tenant_id,
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
            )
        )
        return list(self.db.scalars(stmt).all())

    def get_user_permissions(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> set[str]:
        """Union of permission codes across all user roles."""
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                UserRole.tenant_id == tenant_id,
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                RolePermission.tenant_id == tenant_id,
                RolePermission.deleted_at.is_(None),
                Permission.tenant_id == tenant_id,
                Permission.deleted_at.is_(None),
            )
            .distinct()
        )
        return set(self.db.scalars(stmt).all())

    def assign_role_to_user(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> UserRole:
        existing = self.db.scalars(
            select(UserRole).where(
                UserRole.tenant_id == tenant_id,
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.deleted_at.is_(None),
            )
        ).first()
        if existing:
            return existing
        row = UserRole(tenant_id=tenant_id, user_id=user_id, role_id=role_id)
        self.db.add(row)
        return row


class TenantRbacRepository(TenantScopedRepository):
    """Tenant-scoped RBAC helpers."""

    def user_has_role(self, user_id: uuid.UUID, role_code: str) -> bool:
        repo = RbacRepository(self.db)
        role = repo.get_role_by_code(self.tenant_id, role_code)
        if role is None:
            return False
        stmt = select(UserRole).where(
            UserRole.tenant_id == self.tenant_id,
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
            UserRole.deleted_at.is_(None),
        )
        return self.db.scalars(stmt).first() is not None
