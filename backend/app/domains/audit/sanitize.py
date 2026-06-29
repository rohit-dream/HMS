"""Redact sensitive fields before persisting audit payloads."""

from __future__ import annotations

from typing import Any

REDACTED = "***REDACTED***"

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "password_confirmation",
        "current_password",
        "new_password",
        "access_token",
        "refresh_token",
        "token",
        "secret",
        "api_key",
        "captcha_token",
        "otp",
        "pin",
    }
)

_SENSITIVE_SUFFIXES = ("_password", "_token", "_secret", "_api_key")

# PHI fields redacted from mutation audit payloads (DPDP / SECURITY_ARCHITECTURE §11).
_PHI_KEYS = frozenset(
    {
        "first_name",
        "last_name",
        "phone",
        "email",
        "date_of_birth",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "id_proof_number",
        "id_proof_type",
        "allergen",
        "reaction",
        "occupation",
        "marital_status",
        "blood_group",
        "photo_url",
        "chief_complaint",
        "diagnosis",
        "notes",
        "condition_name",
        "icd_code",
    }
)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    if normalized in _SENSITIVE_KEYS:
        return True
    if normalized in _PHI_KEYS:
        return True
    return any(normalized.endswith(suffix) for suffix in _SENSITIVE_SUFFIXES)


def sanitize_audit_values(values: Any) -> Any:
    """Recursively redact passwords, tokens, and secrets from audit JSON payloads."""
    if values is None:
        return None
    if isinstance(values, list):
        return [sanitize_audit_values(item) for item in values]
    if not isinstance(values, dict):
        return values

    sanitized: dict[str, Any] = {}
    for key, value in values.items():
        if _is_sensitive_key(key):
            sanitized[key] = REDACTED
        elif isinstance(value, dict):
            sanitized[key] = sanitize_audit_values(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_audit_values(value)
        else:
            sanitized[key] = value
    return sanitized
