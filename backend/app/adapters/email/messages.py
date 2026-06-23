"""Email message types for transactional notifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EmailTemplate(StrEnum):
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    USER_INVITE = "user_invite"
    WELCOME = "welcome"


# Legacy caplog prefixes used by auth integration tests.
LEGACY_LOG_PREFIX: dict[EmailTemplate, str | None] = {
    EmailTemplate.PASSWORD_RESET: "password_reset_token_issued",
    EmailTemplate.EMAIL_VERIFICATION: "email_verification_token_issued",
    EmailTemplate.USER_INVITE: "user_invite_token_issued",
    EmailTemplate.WELCOME: None,
}


@dataclass(frozen=True)
class EmailMessage:
    to_email: str
    subject: str
    text_body: str
    html_body: str
    template: EmailTemplate
    tenant_id: str | None = None
    tenant_slug: str | None = None
    token: str | None = None
    action_url: str | None = None
