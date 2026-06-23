"""Unit tests for auth rate limiting."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request

from app.core.config import Settings
from app.core.constants import AUTH_RATE_LIMIT_PREFIX
from app.core.exceptions import RateLimitExceededError
from app.core.rate_limit import check_auth_rate_limit


@pytest.fixture
def rate_limit_settings() -> Settings:
    return Settings(
        environment="staging",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
        auth_rate_limit_per_minute=10,
    )


def _request_with_ip(ip: str = "203.0.113.10") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/auth/login",
        "headers": [],
        "client": (ip, 12345),
    }
    return Request(scope)


@patch("app.core.rate_limit.get_redis")
def test_check_auth_rate_limit_sets_expiry_on_first_hit(
    mock_get_redis: MagicMock,
    rate_limit_settings: Settings,
) -> None:
    redis_client = MagicMock()
    redis_client.incr.return_value = 1
    mock_get_redis.return_value = redis_client

    check_auth_rate_limit(_request_with_ip(), rate_limit_settings)

    redis_client.incr.assert_called_once_with(f"{AUTH_RATE_LIMIT_PREFIX}203.0.113.10")
    redis_client.expire.assert_called_once_with(f"{AUTH_RATE_LIMIT_PREFIX}203.0.113.10", 60)


@patch("app.core.rate_limit.get_redis")
def test_check_auth_rate_limit_allows_under_threshold(
    mock_get_redis: MagicMock,
    rate_limit_settings: Settings,
) -> None:
    redis_client = MagicMock()
    redis_client.incr.return_value = 10
    mock_get_redis.return_value = redis_client

    check_auth_rate_limit(_request_with_ip(), rate_limit_settings)


@patch("app.core.rate_limit.get_redis")
def test_check_auth_rate_limit_raises_when_exceeded(
    mock_get_redis: MagicMock,
    rate_limit_settings: Settings,
) -> None:
    redis_client = MagicMock()
    redis_client.incr.return_value = 11
    mock_get_redis.return_value = redis_client

    with pytest.raises(RateLimitExceededError, match="Too many authentication attempts"):
        check_auth_rate_limit(_request_with_ip(), rate_limit_settings)


@patch("app.core.rate_limit.get_redis")
def test_check_auth_rate_limit_fails_open_in_test_when_redis_unavailable(
    mock_get_redis: MagicMock,
) -> None:
    mock_get_redis.side_effect = ConnectionError("redis down")
    settings = Settings(
        environment="test",
        database_url="postgresql://hms:hms@localhost:5432/hms_test",
    )

    check_auth_rate_limit(_request_with_ip("127.0.0.1"), settings)
