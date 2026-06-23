"""Pydantic schemas for user management."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.rbac.catalog import TENANT_ROLE_CODES

VALID_USER_STATUSES = frozenset({"active", "inactive", "locked"})


class UserCreateRequest(BaseModel):
    """Create an active user with password (admin provisioning)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    location_id: uuid.UUID | None = None
    role_codes: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("role_codes")
    @classmethod
    def validate_roles(cls, codes: list[str]) -> list[str]:
        normalized = [c.strip().lower() for c in codes]
        invalid = [c for c in normalized if c not in TENANT_ROLE_CODES]
        if invalid:
            raise ValueError(f"Invalid role codes: {', '.join(invalid)}")
        return normalized


class UserInviteRequest(BaseModel):
    """Invite user — created inactive until password is set."""

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    location_id: uuid.UUID | None = None
    role_codes: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("role_codes")
    @classmethod
    def validate_roles(cls, codes: list[str]) -> list[str]:
        normalized = [c.strip().lower() for c in codes]
        invalid = [c for c in normalized if c not in TENANT_ROLE_CODES]
        if invalid:
            raise ValueError(f"Invalid role codes: {', '.join(invalid)}")
        return normalized


class UserUpdateRequest(BaseModel):
    """Admin update of user profile fields."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = None
    location_id: uuid.UUID | None = None
    status: str | None = Field(default=None)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_USER_STATUSES:
            raise ValueError("Status must be active, inactive, or locked")
        return value


class SelfProfileUpdateRequest(BaseModel):
    """Authenticated user updates own profile (non-admin)."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = None


class AssignRoleRequest(BaseModel):
    role_code: str = Field(min_length=1, max_length=50)

    @field_validator("role_code")
    @classmethod
    def normalize_role(cls, value: str) -> str:
        code = value.strip().lower()
        if code not in TENANT_ROLE_CODES:
            raise ValueError(f"Role not assignable to tenant users: {code}")
        return code


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    avatar_url: str | None = None
    status: str
    roles: list[str] = Field(default_factory=list)
    location_id: uuid.UUID | None = None
    staff_id: uuid.UUID | None = None
    last_login_at: datetime | None = None
    email_verified_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserInviteResponse(UserProfileResponse):
    """Invite result — includes one-time token until email adapter sends the link."""

    invite_token: str
    invite_expires_at: datetime


class UserListItem(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    status: str
    roles: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None
