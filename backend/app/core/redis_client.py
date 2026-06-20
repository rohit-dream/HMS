"""Redis client for JWT denylist and auth rate limiting."""

from __future__ import annotations

import redis

from app.core.config import Settings, get_settings

_client: redis.Redis | None = None


def get_redis(settings: Settings | None = None) -> redis.Redis:
    """Return a shared Redis client."""
    global _client
    if _client is None:
        settings = settings or get_settings()
        _client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=settings.redis_connect_timeout_seconds,
            socket_timeout=settings.redis_connect_timeout_seconds,
            decode_responses=True,
        )
    return _client


def reset_redis_client() -> None:
    """Reset client — used in tests."""
    global _client
    if _client is not None:
        _client.close()
    _client = None
