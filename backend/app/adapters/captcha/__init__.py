"""CAPTCHA provider adapters."""

from app.adapters.captcha.hcaptcha import verify_captcha_token

__all__ = ["verify_captcha_token"]
