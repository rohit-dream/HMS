"""hCaptcha server-side verification with dev/test bypass support."""

from __future__ import annotations

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import ValidationError

HCAPTCHA_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


def verify_captcha_token(
    token: str | None,
    *,
    remote_ip: str | None,
    settings: Settings | None = None,
) -> None:
    """Validate CAPTCHA token; raises ValidationError when verification fails."""
    settings = settings or get_settings()
    if settings.captcha_bypass:
        return

    if not token or not token.strip():
        raise ValidationError("CAPTCHA verification is required", field="captcha_token")

    secret = settings.hcaptcha_secret_key
    if not secret:
        if settings.is_development or settings.is_test:
            return
        raise ValidationError("CAPTCHA verification is not configured", field="captcha_token")

    try:
        response = httpx.post(
            HCAPTCHA_VERIFY_URL,
            data={
                "secret": secret,
                "response": token,
                "remoteip": remote_ip or "",
            },
            timeout=settings.captcha_verify_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ValidationError("CAPTCHA verification failed", field="captcha_token") from exc

    if not payload.get("success"):
        raise ValidationError("CAPTCHA verification failed", field="captcha_token")
