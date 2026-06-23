"""Log-only email adapter for development and test environments."""

from __future__ import annotations

import logging

from app.adapters.email.base import EmailAdapter
from app.adapters.email.messages import LEGACY_LOG_PREFIX, EmailMessage

logger = logging.getLogger(__name__)


class LoggingEmailAdapter:
    """Writes email payloads to application logs instead of sending."""

    def send(self, message: EmailMessage) -> None:
        logger.info(
            "email_sent template=%s to=%s tenant_id=%s tenant_slug=%s action_url=%s subject=%s",
            message.template.value,
            message.to_email,
            message.tenant_id,
            message.tenant_slug,
            message.action_url,
            message.subject,
        )
        legacy_prefix = LEGACY_LOG_PREFIX.get(message.template)
        if legacy_prefix and message.token and message.tenant_id:
            logger.info(
                "%s email=%s tenant_id=%s token=%s",
                legacy_prefix,
                message.to_email,
                message.tenant_id,
                message.token,
            )
