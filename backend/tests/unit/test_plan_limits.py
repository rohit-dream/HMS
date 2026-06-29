"""Unit tests — trial plan patient cap enforcement."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import PlanLimitError
from app.core.tenant.limits import assert_trial_patient_capacity


def test_assert_trial_patient_capacity_skips_non_trial_tenants() -> None:
    db = MagicMock()
    tenant = MagicMock(status="active")
    with patch("app.core.tenant.limits.TenantRepository") as tenant_repo_cls:
        tenant_repo_cls.return_value.get_by_id.return_value = tenant
        assert_trial_patient_capacity(db, uuid.uuid4(), patient_limit=1)


def test_assert_trial_patient_capacity_raises_at_limit() -> None:
    db = MagicMock()
    tenant = MagicMock(status="trial")
    with (
        patch("app.core.tenant.limits.TenantRepository") as tenant_repo_cls,
        patch("app.core.tenant.limits.PatientRepository") as patient_repo_cls,
    ):
        tenant_repo_cls.return_value.get_by_id.return_value = tenant
        patient_repo_cls.return_value.count_active.return_value = 2

        with pytest.raises(PlanLimitError) as exc_info:
            assert_trial_patient_capacity(db, uuid.uuid4(), patient_limit=2)

    assert exc_info.value.code == "plan_limit_patients"
    assert exc_info.value.field == "patients"


def test_assert_trial_patient_capacity_allows_below_limit() -> None:
    db = MagicMock()
    tenant = MagicMock(status="trial")
    with (
        patch("app.core.tenant.limits.TenantRepository") as tenant_repo_cls,
        patch("app.core.tenant.limits.PatientRepository") as patient_repo_cls,
    ):
        tenant_repo_cls.return_value.get_by_id.return_value = tenant
        patient_repo_cls.return_value.count_active.return_value = 1
        assert_trial_patient_capacity(db, uuid.uuid4(), patient_limit=2)
