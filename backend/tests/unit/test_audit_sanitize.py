"""Unit tests — audit value sanitization (MVP-053)."""

from __future__ import annotations

from app.domains.audit.sanitize import REDACTED, sanitize_audit_values


def test_sanitize_redacts_password_fields() -> None:
    result = sanitize_audit_values(
        {
            "display_name": "Admin User",
            "password": "Secret@123",
            "password_hash": "bcrypt-hash",
            "new_password": "New@456",
        }
    )
    assert result["display_name"] == "Admin User"
    assert result["password"] == REDACTED
    assert result["password_hash"] == REDACTED
    assert result["new_password"] == REDACTED


def test_sanitize_redacts_email_as_phi() -> None:
    result = sanitize_audit_values({"email": "user@example.com"})
    assert result["email"] == REDACTED


def test_sanitize_redacts_tokens_and_secrets() -> None:
    result = sanitize_audit_values(
        {
            "access_token": "jwt-access",
            "refresh_token": "jwt-refresh",
            "api_key": "key-123",
            "captcha_token": "captcha",
        }
    )
    assert result == {
        "access_token": REDACTED,
        "refresh_token": REDACTED,
        "api_key": REDACTED,
        "captcha_token": REDACTED,
    }


def test_sanitize_redacts_nested_and_list_values() -> None:
    result = sanitize_audit_values(
        {
            "profile": {"user_token": "nested"},
            "items": [{"secret": "value"}, {"name": "ok"}],
        }
    )
    assert result["profile"]["user_token"] == REDACTED
    assert result["items"][0]["secret"] == REDACTED
    assert result["items"][1]["name"] == "ok"


def test_sanitize_redacts_phi_fields() -> None:
    result = sanitize_audit_values(
        {
            "first_name": "Anita",
            "phone": "9876543210",
            "date_of_birth": "1990-01-01",
            "mrn": "MRN-2026-00001",
        }
    )
    assert result["first_name"] == REDACTED
    assert result["phone"] == REDACTED
    assert result["date_of_birth"] == REDACTED
    assert result["mrn"] == "MRN-2026-00001"


def test_sanitize_returns_none_for_none_input() -> None:
    assert sanitize_audit_values(None) is None
