"""Pydantic schemas for platform tenant and hospital management."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(value: str) -> str:
    normalized = value.strip().lower()
    if not _SLUG_PATTERN.match(normalized):
        raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
    if len(normalized) < 3 or len(normalized) > 100:
        raise ValueError("Slug must be between 3 and 100 characters")
    return normalized


class TenantRegisterRequest(BaseModel):
    """Public tenant registration / provisioning."""

    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=3, max_length=100)
    email: EmailStr
    subdomain: str | None = Field(default=None, max_length=100)
    country: str = Field(default="IN", max_length=100)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    owner_first_name: str = Field(min_length=1, max_length=100)
    owner_last_name: str = Field(min_length=1, max_length=100)
    owner_password: str = Field(min_length=8, max_length=128)
    captcha_token: str | None = Field(default=None, max_length=4096)
    accept_terms: bool = Field(description="Must be true — Terms of Service acceptance")
    accept_privacy_policy: bool = Field(description="Must be true — Privacy Policy acceptance")

    @model_validator(mode="after")
    def require_legal_acceptance(self) -> TenantRegisterRequest:
        if not self.accept_terms:
            raise ValueError("Terms of Service must be accepted")
        if not self.accept_privacy_policy:
            raise ValueError("Privacy Policy must be accepted")
        return self

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return validate_slug(value)

    @field_validator("subdomain")
    @classmethod
    def normalize_subdomain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_slug(value)


class TenantCreateRequest(BaseModel):
    """Platform-admin tenant creation (no owner user)."""

    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=3, max_length=100)
    email: EmailStr
    subdomain: str | None = Field(default=None, max_length=100)
    country: str = Field(default="IN", max_length=100)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return validate_slug(value)


class TenantStatusActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    subdomain: str | None
    status: str
    email: str
    phone: str | None = None
    country: str
    timezone: str
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantRegisterResponse(BaseModel):
    tenant: TenantResponse
    trial_ends_at: datetime | None = None


class LegalVersionsResponse(BaseModel):
    terms_version: str
    privacy_policy_version: str
    terms_url: str
    privacy_policy_url: str


class HospitalProfileResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    email: str
    phone: str | None = None
    logo_url: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str
    tax_registration_no: str | None = None
    timezone: str
    currency: str
    status: str

    model_config = {"from_attributes": True}


class HospitalProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    logo_url: str | None = None
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    tax_registration_no: str | None = Field(default=None, max_length=50)
    timezone: str | None = Field(default=None, max_length=50)
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class LocationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=20)
    is_primary: bool = False
    address_line1: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class LocationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address_line1: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    is_primary: bool | None = None
    is_active: bool | None = None


class LocationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    code: str
    is_primary: bool
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    phone: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class SettingResponse(BaseModel):
    setting_key: str
    setting_value: dict[str, Any]
    description: str | None = None

    model_config = {"from_attributes": True}


class SettingUpsertRequest(BaseModel):
    setting_value: dict[str, Any]
    description: str | None = None


class SettingsBulkUpdateRequest(BaseModel):
    settings: dict[str, dict[str, Any]]
