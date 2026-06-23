"""Default tenant settings seeded on provisioning."""

from __future__ import annotations

ONBOARDING_PROGRESS_DEFAULT: dict = {
    "email_verified": False,
    "profile_complete": False,
    "departments_added": False,
    "staff_invited": False,
    "services_configured": False,
    "first_patient_registered": False,
    "completed_at": None,
}

CLINICAL_SETTINGS_DEFAULT: dict = {
    "vitals_unit": "metric",
    "temperature_unit": "celsius",
    "default_consultation_duration_minutes": 15,
    "mrn_prefix": "MRN",
}

BILLING_SETTINGS_DEFAULT: dict = {
    "invoice_prefix": "INV",
    "receipt_prefix": "RCP",
    "currency_display": "INR",
    "tax_inclusive_pricing": False,
    "tax_rate": 18.0,
}

SYSTEM_SETTINGS_DEFAULT: dict = {
    "date_format": "DD/MM/YYYY",
}

DEFAULT_TENANT_SETTINGS: dict[str, tuple[dict, str]] = {
    "onboarding_progress": (ONBOARDING_PROGRESS_DEFAULT, "Onboarding wizard progress"),
    "clinical": (CLINICAL_SETTINGS_DEFAULT, "Clinical workflow defaults"),
    "billing": (BILLING_SETTINGS_DEFAULT, "Billing and invoicing defaults"),
    "system": (SYSTEM_SETTINGS_DEFAULT, "System display and formatting defaults"),
}

PRIMARY_LOCATION_CODE = "MAIN"
PRIMARY_LOCATION_NAME = "Main Branch"

# NFR-COMP-008 — versioned legal documents accepted at signup.
CURRENT_TERMS_VERSION = "2026-01"
CURRENT_PRIVACY_POLICY_VERSION = "2026-01"
LEGAL_ACCEPTANCE_SETTING_KEY = "legal_acceptance"

RESERVED_TENANT_SLUGS = frozenset({
    "admin", "api", "app", "assets", "auth", "billing", "dashboard",
    "docs", "health", "help", "login", "platform", "register", "static",
    "support", "system", "www",
})

VALID_TENANT_STATUSES = frozenset({"trial", "active", "past_due", "suspended", "cancelled"})
ACTIVATABLE_STATUSES = frozenset({"trial", "past_due", "suspended"})
SUSPENDABLE_STATUSES = frozenset({"trial", "active", "past_due"})
