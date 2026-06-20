"""Unit tests for tenant schema validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domains.platform.schemas.tenant import TenantRegisterRequest, validate_slug


def test_validate_slug_accepts_valid() -> None:
    assert validate_slug("apollo-clinic") == "apollo-clinic"


def test_validate_slug_normalizes_to_lowercase() -> None:
    assert validate_slug("Apollo-Clinic") == "apollo-clinic"


def test_register_request_normalizes_slug() -> None:
    req = TenantRegisterRequest(
        name="Test",
        slug="My-Clinic-01",
        email="a@b.com",
        owner_first_name="A",
        owner_last_name="B",
        owner_password="password123",
    )
    assert req.slug == "my-clinic-01"


def test_register_request_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        TenantRegisterRequest(
            name="Test",
            slug="valid-slug",
            email="a@b.com",
            owner_first_name="A",
            owner_last_name="B",
            owner_password="short",
        )
