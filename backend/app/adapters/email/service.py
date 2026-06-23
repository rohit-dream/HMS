"""High-level transactional email notifications."""

from __future__ import annotations

import logging
import uuid

from app.adapters.email.base import EmailAdapter
from app.adapters.email.factory import get_email_adapter
from app.adapters.email.templates import (
    build_email_verification_email,
    build_password_reset_email,
    build_user_invite_email,
    build_welcome_email,
)
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Send transactional emails without failing the calling business transaction."""

    def __init__(
        self,
        settings: Settings | None = None,
        adapter: EmailAdapter | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._adapter = adapter or get_email_adapter(self.settings)

    def send_password_reset(
        self,
        *,
        to_email: str,
        token: str,
        tenant_id: uuid.UUID,
        tenant_slug: str,
    ) -> None:
        self._send_safe(
            build_password_reset_email(
                self.settings,
                to_email=to_email,
                token=token,
                tenant_id=str(tenant_id),
                tenant_slug=tenant_slug,
            )
        )

    def send_email_verification(
        self,
        *,
        to_email: str,
        token: str,
        tenant_id: uuid.UUID,
        tenant_slug: str,
    ) -> None:
        self._send_safe(
            build_email_verification_email(
                self.settings,
                to_email=to_email,
                token=token,
                tenant_id=str(tenant_id),
                tenant_slug=tenant_slug,
            )
        )

    def send_user_invite(
        self,
        *,
        to_email: str,
        token: str,
        tenant_id: uuid.UUID,
        tenant_slug: str,
        hospital_name: str,
    ) -> None:
        self._send_safe(
            build_user_invite_email(
                self.settings,
                to_email=to_email,
                token=token,
                tenant_id=str(tenant_id),
                tenant_slug=tenant_slug,
                hospital_name=hospital_name,
            )
        )

    def send_welcome(
        self,
        *,
        to_email: str,
        tenant_slug: str,
        hospital_name: str,
    ) -> None:
        self._send_safe(
            build_welcome_email(
                self.settings,
                to_email=to_email,
                tenant_slug=tenant_slug,
                hospital_name=hospital_name,
            )
        )

    def _send_safe(self, message) -> None:
        try:
            self._adapter.send(message)
        except Exception:
            logger.exception(
                "email_delivery_failed template=%s to=%s tenant_id=%s",
                message.template.value,
                message.to_email,
                message.tenant_id,
            )
