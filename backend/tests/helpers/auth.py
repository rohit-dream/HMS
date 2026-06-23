"""Shared helpers for auth integration and E2E tests."""

from __future__ import annotations

import uuid


def register_payload(*, suffix: str | None = None) -> dict:
    token = suffix or uuid.uuid4().hex[:8]
    return {
        "name": f"E2E Clinic {token}",
        "slug": f"e2e-clinic-{token}",
        "email": f"owner-{token}@example.com",
        "owner_first_name": "E2E",
        "owner_last_name": "Owner",
        "owner_password": "SecurePass@123",
        "accept_terms": True,
        "accept_privacy_policy": True,
    }


def token_from_caplog(caplog, prefix: str, email: str) -> str | None:
    template = f"{prefix} email=%s tenant_id=%s token=%s"
    for record in caplog.records:
        if getattr(record, "msg", None) == template and record.args and record.args[0] == email:
            return record.args[2]
        message = record.getMessage()
        if message.startswith(prefix) and email in message:
            return message.rsplit("token=", 1)[-1]
    return None
