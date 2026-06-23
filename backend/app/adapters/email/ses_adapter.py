"""AWS SES email adapter (stub — uses boto3 when configured)."""

from __future__ import annotations

import logging

from app.adapters.email.logging_adapter import LoggingEmailAdapter
from app.adapters.email.messages import EmailMessage
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SesEmailAdapter:
    """Send email via AWS SES; falls back to logging when SES is unavailable."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._fallback = LoggingEmailAdapter()

    def send(self, message: EmailMessage) -> None:
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError as exc:
            logger.warning("boto3 unavailable for SES (%s) — using log fallback", exc)
            self._fallback.send(message)
            return

        try:
            client = boto3.client("ses", region_name=self.settings.aws_region)
            client.send_email(
                Source=self.settings.ses_from_email,
                Destination={"ToAddresses": [message.to_email]},
                Message={
                    "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": message.text_body, "Charset": "UTF-8"},
                        "Html": {"Data": message.html_body, "Charset": "UTF-8"},
                    },
                },
            )
            logger.info(
                "ses_email_sent template=%s to=%s tenant_id=%s",
                message.template.value,
                message.to_email,
                message.tenant_id,
            )
        except (ClientError, BotoCoreError, Exception) as exc:
            logger.warning(
                "ses_email_failed template=%s to=%s error=%s — using log fallback",
                message.template.value,
                message.to_email,
                exc,
            )
            self._fallback.send(message)
