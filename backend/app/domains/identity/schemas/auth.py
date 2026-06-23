"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserSummary(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    roles: list[str]
    tenant_id: uuid.UUID


class LoginResponseData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class TokenResponseData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponseData(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    roles: list[str]
    permissions: list[str] = Field(default_factory=list)
    tenant_id: uuid.UUID
    staff_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class AcceptInviteRequest(BaseModel):
    invite_token: str = Field(min_length=1, max_length=512)
    password: str = Field(min_length=8, max_length=128)


class MessageResponseData(BaseModel):
    message: str
