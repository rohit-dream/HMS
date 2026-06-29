"""Plan limit enforcement — trial caps and subscription quotas."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PlanLimitError
from app.db.subscription_plan_catalog import TRIAL_PATIENT_LIMIT
from app.domains.patients.repositories.patient_repository import PatientRepository
from app.domains.platform.repositories.tenant_repository import TenantRepository


def assert_trial_patient_capacity(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    patient_limit: int | None = None,
) -> None:
    """Raise PlanLimitError when a trial tenant has reached the patient cap."""
    tenant = TenantRepository(db).get_by_id(tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant not found", field="tenant_id")

    if tenant.status != "trial":
        return

    limit = patient_limit if patient_limit is not None else TRIAL_PATIENT_LIMIT
    count = PatientRepository(db, tenant_id).count_active()
    if count >= limit:
        raise PlanLimitError(
            f"Trial plan allows a maximum of {limit} patients. Upgrade to add more.",
            resource="patients",
        )
