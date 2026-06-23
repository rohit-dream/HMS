"""Frontend action URLs for transactional email templates."""

from __future__ import annotations

from urllib.parse import urlencode

from app.adapters.email.messages import EmailTemplate
from app.core.config import Settings


def build_action_url(
    settings: Settings,
    *,
    template: EmailTemplate,
    token: str,
    tenant_slug: str,
) -> str:
    base = settings.frontend_base_url.rstrip("/")
    path_map = {
        EmailTemplate.PASSWORD_RESET: "/reset-password",
        EmailTemplate.EMAIL_VERIFICATION: "/verify-email",
        EmailTemplate.USER_INVITE: "/accept-invite",
    }
    path = path_map.get(template)
    if path is None:
        raise ValueError(f"Template {template} does not have an action URL")

    query = urlencode({"token": token, "tenant": tenant_slug})
    return f"{base}{path}?{query}"
