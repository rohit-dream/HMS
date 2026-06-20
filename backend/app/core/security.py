"""
JWT RS256, password hashing, refresh tokens, and Redis denylist.

Per AUTHENTICATION_ARCHITECTURE_GUIDE.md:
- Access JWT: RS256, 30 min, claims sub/tenant_id/roles/jti (no permissions)
- Refresh: opaque token, SHA-256 hash stored server-side
- Passwords: bcrypt cost 12
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import bcrypt
import jwt

from app.core.config import Settings, get_settings
from app.core.constants import (
    BCRYPT_ROUNDS,
    JWT_ALGORITHM,
    JWT_DENYLIST_PREFIX,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.core.redis_client import get_redis


@dataclass(frozen=True)
class AccessTokenClaims:
    """Validated access token payload."""

    sub: uuid.UUID
    tenant_id: uuid.UUID
    roles: tuple[str, ...]
    jti: uuid.UUID
    exp: datetime
    iss: str


def hash_password(plain_password: str) -> str:
    """Hash password with bcrypt (cost 12)."""
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify plain password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def generate_refresh_token() -> str:
    """Generate cryptographically secure opaque refresh token (256+ bits)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash of refresh token for database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@lru_cache
def _load_private_key(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


@lru_cache
def _load_public_key(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def create_access_token(
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    roles: list[str] | None = None,
    settings: Settings | None = None,
) -> tuple[str, uuid.UUID, int]:
    """
    Create RS256 access JWT.

    Returns (token, jti, expires_in_seconds).
    """
    settings = settings or get_settings()
    jti = uuid.uuid4()
    now = datetime.now(UTC)
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    exp = now + expires_delta

    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "roles": roles or [],
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(jti),
    }

    private_key = _load_private_key(settings.jwt_private_key_path)
    token = jwt.encode(payload, private_key, algorithm=JWT_ALGORITHM)
    return token, jti, int(expires_delta.total_seconds())


def decode_access_token(token: str, settings: Settings | None = None) -> AccessTokenClaims:
    """Validate and decode access JWT. Raises jwt.PyJWTError on failure."""
    settings = settings or get_settings()
    public_key = _load_public_key(settings.jwt_public_key_path)
    payload = jwt.decode(
        token,
        public_key,
        algorithms=[JWT_ALGORITHM],
        issuer=settings.jwt_issuer,
    )
    return AccessTokenClaims(
        sub=uuid.UUID(payload["sub"]),
        tenant_id=uuid.UUID(payload["tenant_id"]),
        roles=tuple(payload.get("roles") or []),
        jti=uuid.UUID(payload["jti"]),
        exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
        iss=payload["iss"],
    )


def is_token_denied(jti: uuid.UUID, settings: Settings | None = None) -> bool:
    """Return True if jti is in Redis denylist."""
    settings = settings or get_settings()
    try:
        client = get_redis(settings)
        return bool(client.exists(f"{JWT_DENYLIST_PREFIX}{jti}"))
    except Exception:
        if settings.is_development or settings.is_test:
            return False
        raise


def denylist_access_token(jti: uuid.UUID, expires_at: datetime, settings: Settings | None = None) -> None:
    """Add access token jti to Redis denylist until natural expiry."""
    settings = settings or get_settings()
    ttl = max(int((expires_at - datetime.now(UTC)).total_seconds()), 1)
    try:
        client = get_redis(settings)
        client.setex(f"{JWT_DENYLIST_PREFIX}{jti}", ttl, "1")
    except Exception:
        if settings.is_development or settings.is_test:
            return
        raise


def refresh_token_expires_at(settings: Settings | None = None) -> datetime:
    """Compute refresh token expiry timestamp."""
    settings = settings or get_settings()
    days = settings.jwt_refresh_token_expire_days or REFRESH_TOKEN_EXPIRE_DAYS
    return datetime.now(UTC) + timedelta(days=days)


def clear_key_cache() -> None:
    """Clear cached PEM keys — for tests."""
    _load_private_key.cache_clear()
    _load_public_key.cache_clear()
