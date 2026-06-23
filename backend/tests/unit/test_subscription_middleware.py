"""Unit tests — MVP-044 subscription status policy."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import ForbiddenError, TenantSuspendedError
from app.core.tenant.subscription import (
    assert_tenant_can_authenticate,
    enforce_tenant_subscription,
    is_past_due_mutation_exempt,
)
from app.models.platform.tenant import Tenant


def _tenant(status: str) -> Tenant:
    tenant_id = uuid.uuid4()
    return Tenant(
        id=tenant_id,
        tenant_id=tenant_id,
        name="Test Clinic",
        slug="test-clinic",
        status=status,
        email="admin@test.com",
    )


def test_assert_tenant_can_authenticate_allows_trial_and_active() -> None:
    assert_tenant_can_authenticate(_tenant("trial"))
    assert_tenant_can_authenticate(_tenant("active"))
    assert_tenant_can_authenticate(_tenant("past_due"))


def test_assert_tenant_can_authenticate_blocks_suspended() -> None:
    with pytest.raises(TenantSuspendedError):
        assert_tenant_can_authenticate(_tenant("suspended"))


def test_past_due_blocks_patch_but_allows_get() -> None:
    request = MagicMock()
    request.method = "PATCH"
    request.url.path = "/api/v1/hospital/profile"

    with pytest.raises(ForbiddenError) as exc:
        enforce_tenant_subscription(request, _tenant("past_due"), api_v1_prefix="/api/v1")
    assert exc.value.field == "subscription"

    request.method = "GET"
    enforce_tenant_subscription(request, _tenant("past_due"), api_v1_prefix="/api/v1")


def test_past_due_logout_mutation_is_exempt() -> None:
    assert is_past_due_mutation_exempt("/api/v1/auth/logout", "/api/v1") is True

    request = MagicMock()
    request.method = "POST"
    request.url.path = "/api/v1/auth/logout"
    enforce_tenant_subscription(request, _tenant("past_due"), api_v1_prefix="/api/v1")
