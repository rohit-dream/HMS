"""Unit tests for hCaptcha verification adapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.adapters.captcha.hcaptcha import verify_captcha_token
from app.core.config import Settings
from app.core.exceptions import ValidationError


@pytest.fixture
def captcha_settings() -> Settings:
    return Settings(
        environment="staging",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
        captcha_bypass=False,
        hcaptcha_secret_key="test-secret",
    )


def test_verify_captcha_bypass_skips_validation() -> None:
    settings = Settings(
        environment="staging",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
        captcha_bypass=True,
        hcaptcha_secret_key="",
    )
    verify_captcha_token(None, remote_ip="127.0.0.1", settings=settings)


def test_verify_captcha_requires_token(captcha_settings: Settings) -> None:
    with pytest.raises(ValidationError, match="CAPTCHA verification is required"):
        verify_captcha_token(None, remote_ip="127.0.0.1", settings=captcha_settings)


@patch("app.adapters.captcha.hcaptcha.httpx.post")
def test_verify_captcha_accepts_valid_response(mock_post: MagicMock, captcha_settings: Settings) -> None:
    response = MagicMock()
    response.json.return_value = {"success": True}
    response.raise_for_status = MagicMock()
    mock_post.return_value = response

    verify_captcha_token("valid-token", remote_ip="127.0.0.1", settings=captcha_settings)
    mock_post.assert_called_once()


@patch("app.adapters.captcha.hcaptcha.httpx.post")
def test_verify_captcha_rejects_failed_response(mock_post: MagicMock, captcha_settings: Settings) -> None:
    response = MagicMock()
    response.json.return_value = {"success": False}
    response.raise_for_status = MagicMock()
    mock_post.return_value = response

    with pytest.raises(ValidationError, match="CAPTCHA verification failed"):
        verify_captcha_token("bad-token", remote_ip="127.0.0.1", settings=captcha_settings)


@patch("app.adapters.captcha.hcaptcha.httpx.post")
def test_verify_captcha_rejects_http_error(mock_post: MagicMock, captcha_settings: Settings) -> None:
    mock_post.side_effect = httpx.HTTPError("network error")

    with pytest.raises(ValidationError, match="CAPTCHA verification failed"):
        verify_captcha_token("token", remote_ip="127.0.0.1", settings=captcha_settings)
