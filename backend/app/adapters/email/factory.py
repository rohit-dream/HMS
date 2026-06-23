"""Email adapter factory."""

from __future__ import annotations

from functools import lru_cache

from app.adapters.email.base import EmailAdapter
from app.adapters.email.logging_adapter import LoggingEmailAdapter
from app.adapters.email.ses_adapter import SesEmailAdapter
from app.core.config import Settings, get_settings


def get_email_adapter(settings: Settings | None = None) -> EmailAdapter:
    settings = settings or get_settings()
    if settings.email_provider == "ses":
        return SesEmailAdapter(settings)
    return LoggingEmailAdapter()


@lru_cache
def get_cached_email_adapter() -> EmailAdapter:
    return get_email_adapter(get_settings())
