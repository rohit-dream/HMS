"""Shared patient API test payloads."""

from __future__ import annotations

CONSENT_DEFAULTS: dict[str, object] = {
    "data_processing_consent": True,
    "consent_method": "digital",
}


def minimal_patient_payload(**overrides: object) -> dict:
    """Minimal valid POST /patients body for integration tests."""
    payload = {
        "first_name": "Anita",
        "last_name": "Sharma",
        "date_of_birth": "1990-03-15",
        "gender": "female",
        "phone": "9876543210",
        **CONSENT_DEFAULTS,
    }
    payload.update(overrides)
    return payload
