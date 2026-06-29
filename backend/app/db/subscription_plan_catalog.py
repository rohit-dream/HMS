"""Canonical subscription plan definitions — single source for seeds and docs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.constants import SYSTEM_TENANT_ID

PLAN_CODE_STARTER = "starter"
PLAN_CODE_PROFESSIONAL = "professional"
PLAN_CODE_ENTERPRISE = "enterprise"

PLAN_CODES: frozenset[str] = frozenset({
    PLAN_CODE_STARTER,
    PLAN_CODE_PROFESSIONAL,
    PLAN_CODE_ENTERPRISE,
})


@dataclass(frozen=True)
class SubscriptionPlanSeed:
    code: str
    name: str
    description: str
    price_monthly: Decimal
    price_annual: Decimal | None
    max_users: int
    max_beds: int | None
    max_patients: int | None
    features: dict[str, Any]


def _starter_features() -> dict[str, Any]:
    return {
        "modules": {
            "opd": True,
            "patient": True,
            "billing": True,
            "ipd": False,
            "laboratory": False,
            "pharmacy": False,
            "reports_advanced": False,
            "api_access": False,
            "custom_branding": False,
        },
        "limits": {
            "max_users": 10,
            "max_beds": None,
            "max_patients_trial": 100,
            "max_storage_gb": 5,
            "max_locations": 1,
        },
        "support": {"priority": False, "sla_percent": None},
    }


def _professional_features() -> dict[str, Any]:
    return {
        "modules": {
            "opd": True,
            "patient": True,
            "billing": True,
            "ipd": True,
            "laboratory": True,
            "pharmacy": True,
            "reports_advanced": True,
            "api_access": False,
            "custom_branding": False,
        },
        "limits": {
            "max_users": 50,
            "max_beds": 50,
            "max_patients_trial": None,
            "max_storage_gb": 25,
            "max_locations": 5,
        },
        "support": {"priority": False, "sla_percent": None},
    }


def _enterprise_features() -> dict[str, Any]:
    return {
        "modules": {
            "opd": True,
            "patient": True,
            "billing": True,
            "ipd": True,
            "laboratory": True,
            "pharmacy": True,
            "reports_advanced": True,
            "api_access": True,
            "custom_branding": True,
        },
        "limits": {
            "max_users": 200,
            "max_beds": 200,
            "max_patients_trial": None,
            "max_storage_gb": 100,
            "max_locations": None,
        },
        "support": {"priority": True, "sla_percent": 99.9},
    }


SUBSCRIPTION_PLAN_CATALOG: tuple[SubscriptionPlanSeed, ...] = (
    SubscriptionPlanSeed(
        code=PLAN_CODE_STARTER,
        name="Starter",
        description="Clinics and small practices with up to 10 users.",
        price_monthly=Decimal("4999.00"),
        price_annual=Decimal("49990.00"),
        max_users=10,
        max_beds=None,
        max_patients=100,
        features=_starter_features(),
    ),
    SubscriptionPlanSeed(
        code=PLAN_CODE_PROFESSIONAL,
        name="Professional",
        description="Small hospitals with IPD, lab, and pharmacy modules.",
        price_monthly=Decimal("14999.00"),
        price_annual=Decimal("149990.00"),
        max_users=50,
        max_beds=50,
        max_patients=None,
        features=_professional_features(),
    ),
    SubscriptionPlanSeed(
        code=PLAN_CODE_ENTERPRISE,
        name="Enterprise",
        description="Medium hospitals and chains — custom pricing and SLA.",
        price_monthly=Decimal("0.00"),
        price_annual=None,
        max_users=200,
        max_beds=200,
        max_patients=None,
        features=_enterprise_features(),
    ),
)

TRIAL_PATIENT_LIMIT: int = _starter_features()["limits"]["max_patients_trial"]

SYSTEM_TENANT_SEED = {
    "id": SYSTEM_TENANT_ID,
    "name": "HMS Platform System",
    "slug": "system",
    "subdomain": "system",
    "status": "active",
    "email": "system@platform.com",
    "country": "IN",
    "timezone": "Asia/Kolkata",
    "currency": "INR",
}
