"""Unit tests — MVP-043 email adapter."""

from __future__ import annotations

import logging
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.email.factory import get_email_adapter
from app.adapters.email.logging_adapter import LoggingEmailAdapter
from app.adapters.email.messages import EmailTemplate
from app.adapters.email.service import EmailNotificationService
from app.adapters.email.templates import build_user_invite_email
from app.adapters.email.urls import build_action_url
from app.core.config import Settings


def test_build_accept_invite_url() -> None:
    settings = Settings(frontend_base_url="http://localhost:5173")
    url = build_action_url(
        settings,
        template=EmailTemplate.USER_INVITE,
        token="abc123",
        tenant_slug="apollo-clinic",
    )
    assert url.startswith("http://localhost:5173/accept-invite?")
    assert "token=abc123" in url
    assert "tenant=apollo-clinic" in url


def test_logging_adapter_emits_legacy_token_log(caplog) -> None:
    settings = Settings(frontend_base_url="http://localhost:5173")
    message = build_user_invite_email(
        settings,
        to_email="invited@example.com",
        token="invite-token",
        tenant_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
        tenant_slug="apollo-clinic",
        hospital_name="Apollo Clinic",
    )

    with caplog.at_level(logging.INFO):
        LoggingEmailAdapter().send(message)

    assert any("email_sent template=user_invite" in r.getMessage() for r in caplog.records)
    assert any("user_invite_token_issued" in r.getMessage() for r in caplog.records)
    assert any("/accept-invite?" in r.getMessage() for r in caplog.records)


def test_email_notification_service_swallows_adapter_errors() -> None:
    failing = MagicMock()
    failing.send.side_effect = RuntimeError("SES down")
    service = EmailNotificationService(adapter=failing)

    service.send_password_reset(
        to_email="user@example.com",
        token="tok",
        tenant_id=uuid.uuid4(),
        tenant_slug="clinic",
    )

    failing.send.assert_called_once()


def test_get_email_adapter_defaults_to_logging() -> None:
    settings = Settings(email_provider="log")
    adapter = get_email_adapter(settings)
    assert isinstance(adapter, LoggingEmailAdapter)


def test_ses_adapter_falls_back_to_logging_on_send_failure(caplog, monkeypatch) -> None:
    import sys

    from app.adapters.email.ses_adapter import SesEmailAdapter

    settings = Settings(email_provider="ses")
    message = build_user_invite_email(
        settings,
        to_email="invited@example.com",
        token="invite-token",
        tenant_id=str(uuid.uuid4()),
        tenant_slug="clinic",
        hospital_name="Clinic",
    )

    fake_client = MagicMock()
    fake_client.send_email.side_effect = RuntimeError("SES unavailable")
    fake_boto3 = MagicMock()
    fake_boto3.client.return_value = fake_client
    fake_exceptions = MagicMock()
    fake_exceptions.ClientError = Exception
    fake_exceptions.BotoCoreError = Exception
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore.exceptions", fake_exceptions)

    with caplog.at_level(logging.INFO):
        SesEmailAdapter(settings).send(message)

    assert any("email_sent template=user_invite" in r.getMessage() for r in caplog.records)
