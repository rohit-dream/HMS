"""Email adapter protocol."""

from __future__ import annotations

from typing import Protocol

from app.adapters.email.messages import EmailMessage


class EmailAdapter(Protocol):
    def send(self, message: EmailMessage) -> None:
        """Deliver a transactional email message."""
