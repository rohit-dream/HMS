"""User management business logic — tenant-scoped admin operations."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.adapters.email import EmailNotificationService
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.permissions import PermissionResolver
from app.core.rbac.catalog import TENANT_ROLE_CODES
from app.core.config import get_settings
from app.core.security import hash_password, hash_refresh_token
from app.domains.identity.constants import (
    HOSPITAL_OWNER_ROLE,
    MAX_HOSPITAL_OWNERS_PER_TENANT,
    PASSWORD_RESET_TOKEN_HOURS,
    PLATFORM_ADMIN_ROLE,
    USER_INVITE_TOKEN_HOURS,
)
from app.domains.identity.repositories.password_reset_repository import PasswordResetRepository
from app.domains.identity.repositories.rbac_repository import RbacRepository
from app.domains.identity.repositories.session_repository import SessionRepository
from app.domains.identity.repositories.user_invite_repository import UserInviteRepository
from app.domains.identity.repositories.user_repository import UserRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository
from app.domains.identity.schemas.user import (
    AdminResetPasswordRequest,
    AssignRoleRequest,
    SelfProfileUpdateRequest,
    UserCreateRequest,
    UserInviteRequest,
    UserInviteResponse,
    UserListItem,
    UserProfileResponse,
    UserUpdateRequest,
)
from app.models.core.user import User


class UserManagementService:
    """Tenant-aware user CRUD, roles, and password management."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._users = UserRepository(db, tenant_id)
        self._rbac = RbacRepository(db)
        self._sessions = SessionRepository(db, tenant_id)
        self._reset_tokens = PasswordResetRepository(db, tenant_id)
        self._invite_tokens = UserInviteRepository(db, tenant_id)
        self._permissions = PermissionResolver(db)
        self._email = EmailNotificationService(get_settings())
        self._tenant_repo = TenantRepository(db)

    def search_users(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UserListItem], int]:
        users, total = self._users.search(query=query, status=status, page=page, page_size=page_size)
        items = [self._to_list_item(user) for user in users]
        return items, total

    def get_user(self, user_id: uuid.UUID) -> UserProfileResponse:
        user = self._get_user_or_404(user_id)
        return self._to_profile(user)

    def create_user(self, payload: UserCreateRequest, *, actor_id: uuid.UUID) -> UserProfileResponse:
        if self._users.email_exists(str(payload.email)):
            raise ConflictError("Email already registered in this tenant", field="email")

        user = self._users.create(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            location_id=payload.location_id,
            status="active",
            created_by=actor_id,
        )
        for role_code in payload.role_codes:
            self._assign_role_internal(user.id, role_code, actor_id=actor_id, commit=False)

        self.db.commit()
        return self._to_profile(user)

    def invite_user(self, payload: UserInviteRequest, *, actor_id: uuid.UUID) -> UserInviteResponse:
        if self._users.email_exists(str(payload.email)):
            raise ConflictError("Email already registered in this tenant", field="email")

        placeholder_password = hash_password(secrets.token_urlsafe(32))
        user = self._users.create(
            email=str(payload.email),
            password_hash=placeholder_password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            location_id=payload.location_id,
            status="inactive",
            created_by=actor_id,
        )
        for role_code in payload.role_codes:
            self._assign_role_internal(user.id, role_code, actor_id=actor_id, commit=False)

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=USER_INVITE_TOKEN_HOURS)
        self._invite_tokens.invalidate_all_for_user(user.id)
        self._invite_tokens.create_token(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=expires_at,
            created_by=actor_id,
        )

        self.db.commit()
        profile = self._to_profile(user)
        tenant = self._tenant_repo.get_by_id(self.tenant_id)
        if tenant is not None:
            self._email.send_user_invite(
                to_email=user.email,
                token=raw_token,
                tenant_id=self.tenant_id,
                tenant_slug=tenant.slug,
                hospital_name=tenant.name,
            )
        return UserInviteResponse(
            **profile.model_dump(),
            invite_token=raw_token,
            invite_expires_at=expires_at,
        )

    def update_user(
        self,
        user_id: uuid.UUID,
        payload: UserUpdateRequest,
        *,
        actor_id: uuid.UUID,
    ) -> UserProfileResponse:
        user = self._get_user_or_404(user_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] == "inactive":
            self._ensure_can_disable(user_id, actor_id)

        if update_data:
            self._users.update_fields(user, updated_by=actor_id, **update_data)

        if update_data.get("status") == "inactive":
            self._sessions.revoke_all_for_user(user.id)

        self.db.commit()
        return self._to_profile(user)

    def disable_user(self, user_id: uuid.UUID, *, actor_id: uuid.UUID) -> UserProfileResponse:
        user = self._get_user_or_404(user_id)
        self._ensure_can_disable(user_id, actor_id)
        self._users.disable(user, disabled_by=actor_id)
        self._sessions.revoke_all_for_user(user.id)
        self.db.commit()
        return self._to_profile(user)

    def assign_role(
        self,
        user_id: uuid.UUID,
        payload: AssignRoleRequest,
        *,
        actor_id: uuid.UUID,
    ) -> UserProfileResponse:
        user = self._get_user_or_404(user_id)
        self._assign_role_internal(user.id, payload.role_code, actor_id=actor_id, commit=True)
        return self._to_profile(user)

    def remove_role(
        self,
        user_id: uuid.UUID,
        role_code: str,
        *,
        actor_id: uuid.UUID,
    ) -> UserProfileResponse:
        user = self._get_user_or_404(user_id)
        role_code = role_code.strip().lower()
        self._ensure_role_assignable(role_code)
        self._ensure_can_remove_role(user_id, role_code, actor_id)

        role = self._rbac.get_role_by_code(self.tenant_id, role_code)
        if role is None:
            raise NotFoundError("Role not found", field="role_code")

        removed = self._rbac.remove_role_from_user(
            self.tenant_id, user.id, role.id, removed_by=actor_id
        )
        if not removed:
            raise NotFoundError("User does not have this role", field="role_code")

        self._permissions.invalidate_user(self.tenant_id, user.id)
        self.db.commit()
        return self._to_profile(user)

    def reset_password(
        self,
        user_id: uuid.UUID,
        payload: AdminResetPasswordRequest,
        *,
        actor_id: uuid.UUID,
    ) -> dict[str, str]:
        user = self._get_user_or_404(user_id)
        self._users.set_password(user, hash_password(payload.new_password), updated_by=actor_id)
        self._sessions.revoke_all_for_user(user.id)
        self._reset_tokens.invalidate_all_for_user(user.id)
        self.db.commit()
        return {"message": "Password reset successfully"}

    def create_password_reset_token(self, user_id: uuid.UUID, *, actor_id: uuid.UUID) -> dict[str, str]:
        """Generate one-time reset token for invited/inactive users (dev — log token)."""
        user = self._get_user_or_404(user_id)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_refresh_token(raw_token)
        expires_at = datetime.now(UTC) + timedelta(hours=PASSWORD_RESET_TOKEN_HOURS)
        self._reset_tokens.invalidate_all_for_user(user.id)
        self._reset_tokens.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=actor_id,
        )
        self.db.commit()
        return {
            "message": "Password reset token created",
            "reset_token": raw_token,
            "expires_at": expires_at.isoformat(),
        }

    def update_self_profile(
        self,
        user_id: uuid.UUID,
        payload: SelfProfileUpdateRequest,
    ) -> UserProfileResponse:
        user = self._get_user_or_404(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError("No fields to update", field="body")
        self._users.update_fields(user, **update_data)
        self.db.commit()
        return self._to_profile(user)

    def _assign_role_internal(
        self,
        user_id: uuid.UUID,
        role_code: str,
        *,
        actor_id: uuid.UUID,
        commit: bool,
    ) -> None:
        role_code = role_code.strip().lower()
        self._ensure_role_assignable(role_code)

        if role_code == HOSPITAL_OWNER_ROLE:
            owner_count = self._rbac.count_users_with_role(self.tenant_id, HOSPITAL_OWNER_ROLE)
            if role_code not in self._rbac.get_user_role_codes(self.tenant_id, user_id):
                if owner_count >= MAX_HOSPITAL_OWNERS_PER_TENANT:
                    raise ValidationError(
                        f"Maximum {MAX_HOSPITAL_OWNERS_PER_TENANT} hospital owners allowed per tenant",
                        field="role_code",
                    )

        role = self._rbac.get_role_by_code(self.tenant_id, role_code)
        if role is None:
            raise NotFoundError(f"Role not found: {role_code}", field="role_code")

        self._rbac.assign_role_to_user(self.tenant_id, user_id, role.id)
        self._permissions.invalidate_user(self.tenant_id, user_id)
        if commit:
            self.db.commit()

    def _ensure_role_assignable(self, role_code: str) -> None:
        if role_code == PLATFORM_ADMIN_ROLE:
            raise ForbiddenError("platform_admin cannot be assigned to tenant users", field="role_code")
        if role_code not in TENANT_ROLE_CODES:
            raise ValidationError(f"Invalid role code: {role_code}", field="role_code")

    def _ensure_can_disable(self, user_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        if user_id == actor_id:
            raise ForbiddenError("Cannot disable your own account", field="user_id")
        if self._user_has_role(user_id, HOSPITAL_OWNER_ROLE):
            owner_count = self._rbac.count_users_with_role(self.tenant_id, HOSPITAL_OWNER_ROLE)
            if owner_count <= 1:
                raise ForbiddenError("Cannot disable the last hospital owner", field="user_id")

    def _ensure_can_remove_role(self, user_id: uuid.UUID, role_code: str, actor_id: uuid.UUID) -> None:
        if role_code == HOSPITAL_OWNER_ROLE:
            if self._user_has_role(user_id, HOSPITAL_OWNER_ROLE):
                owner_count = self._rbac.count_users_with_role(self.tenant_id, HOSPITAL_OWNER_ROLE)
                if owner_count <= 1:
                    raise ForbiddenError("Cannot remove the last hospital owner role", field="role_code")

    def _get_user_or_404(self, user_id: uuid.UUID) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found", field="user_id")
        return user

    def _to_profile(self, user: User) -> UserProfileResponse:
        roles = self._rbac.get_user_role_codes(self.tenant_id, user.id)
        return UserProfileResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            status=user.status,
            roles=roles,
            location_id=user.location_id,
            staff_id=user.staff_id,
            last_login_at=user.last_login_at,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
        )

    def _user_has_role(self, user_id: uuid.UUID, role_code: str) -> bool:
        return role_code in self._rbac.get_user_role_codes(self.tenant_id, user_id)

    def _to_list_item(self, user: User) -> UserListItem:
        roles = self._rbac.get_user_role_codes(self.tenant_id, user.id)
        return UserListItem(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            status=user.status,
            roles=roles,
            last_login_at=user.last_login_at,
        )

