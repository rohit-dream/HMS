"""Structured JSON logging with request correlation support."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings
from app.core.constants import SERVICE_NAME

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
tenant_id_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)


class HMSJsonFormatter(logging.Formatter):
    """JSON log formatter with HMS standard fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id

        tenant_id = tenant_id_ctx.get()
        if tenant_id:
            payload["tenant_id"] = tenant_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure root logger with JSON formatter."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(HMSJsonFormatter())

    level = getattr(logging, settings.log_level, logging.INFO)
    root.setLevel(level)
    handler.setLevel(level)
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(level)


def bind_request_context(request_id: str | None = None, tenant_id: str | None = None) -> None:
    """Bind correlation identifiers to logging context."""
    if request_id is not None:
        request_id_ctx.set(request_id)
    if tenant_id is not None:
        tenant_id_ctx.set(tenant_id)


def clear_request_context() -> None:
    """Clear per-request logging context."""
    request_id_ctx.set(None)
    tenant_id_ctx.set(None)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
