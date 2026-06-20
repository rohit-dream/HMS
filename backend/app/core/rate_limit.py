"""Auth rate limiting via Redis."""

from __future__ import annotations

from fastapi import Request

from app.core.config import Settings, get_settings
from app.core.constants import AUTH_RATE_LIMIT_PREFIX
from app.core.exceptions import RateLimitExceededError
from app.core.redis_client import get_redis


def check_auth_rate_limit(request: Request, settings: Settings | None = None) -> None:
    """Enforce per-IP rate limit on auth endpoints (10/min default)."""
    settings = settings or get_settings()
    client_ip = request.client.host if request.client else "unknown"
    key = f"{AUTH_RATE_LIMIT_PREFIX}{client_ip}"

    try:
        client = get_redis(settings)
        count = client.incr(key)
        if count == 1:
            client.expire(key, 60)
        if count > settings.auth_rate_limit_per_minute:
            raise RateLimitExceededError("Too many authentication attempts. Try again later.")
    except RateLimitExceededError:
        raise
    except Exception:
        if settings.is_development or settings.is_test:
            return
        raise
