"""Transactional email adapters."""

from app.adapters.email.factory import get_email_adapter
from app.adapters.email.service import EmailNotificationService

__all__ = ["EmailNotificationService", "get_email_adapter"]
