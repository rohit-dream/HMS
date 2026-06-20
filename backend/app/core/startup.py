"""Startup validation — environment, connectivity, and folder structure."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from app.core.config import Settings
from app.core.database import check_database_connection
from app.core.logging import get_logger

logger = get_logger(__name__)
_startup_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="startup-check")


@dataclass
class ValidationResult:
    """Aggregated startup validation outcome."""

    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def validate_settings(settings: Settings) -> ValidationResult:
    """Validate required configuration values."""
    result = ValidationResult()

    if not settings.database_url:
        result.add_error("DATABASE_URL is required")

    if not settings.database_url.startswith("postgresql"):
        result.add_warning("DATABASE_URL does not look like a PostgreSQL URL")

    if not settings.redis_url:
        result.add_error("REDIS_URL is required")

    if settings.is_production and settings.environment != "production":
        result.add_warning("ENVIRONMENT mismatch detected")

    if settings.is_production and "localhost" in settings.cors_origins:
        result.add_warning("CORS_ORIGINS includes localhost in production")

    return result


def check_redis_connection(settings: Settings) -> bool:
    """Return True if Redis responds to PING."""
    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=settings.redis_connect_timeout_seconds,
            socket_timeout=settings.redis_connect_timeout_seconds,
        )
        return bool(client.ping())
    except Exception:
        return False


def run_connectivity_checks(settings: Settings) -> tuple[bool, bool]:
    """Run database and Redis checks in parallel (bounded timeouts)."""
    db_future = _startup_executor.submit(check_database_connection, settings)
    redis_future = _startup_executor.submit(check_redis_connection, settings)
    return db_future.result(), redis_future.result()


def run_startup_validation(settings: Settings, *, strict: bool = True) -> ValidationResult:
    """
    Run all startup checks.

    strict=True: database and redis must be reachable (readiness).
    strict=False: log warnings but allow boot (liveness-only scenarios).
    """
    result = validate_settings(settings)

    db_ok, redis_ok = run_connectivity_checks(settings)

    if not db_ok:
        message = "PostgreSQL connection check failed"
        if strict:
            result.add_error(message)
        else:
            result.add_warning(message)

    if not redis_ok:
        message = "Redis connection check failed"
        if strict:
            result.add_error(message)
        else:
            result.add_warning(message)

    for warning in result.warnings:
        logger.warning(warning)

    if result.errors:
        for error in result.errors:
            logger.error(error)

    return result


async def run_startup_validation_async(settings: Settings) -> ValidationResult:
    """Async wrapper used by FastAPI lifespan — non-strict for dev boot."""
    strict = not settings.is_development and not settings.skip_startup_checks
    if settings.skip_startup_checks:
        return validate_settings(settings)
    return await asyncio.to_thread(run_startup_validation, settings, strict=strict)
