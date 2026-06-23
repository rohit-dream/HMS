"""Plain-text and HTML bodies for transactional emails."""

from __future__ import annotations

from app.adapters.email.messages import EmailMessage, EmailTemplate
from app.adapters.email.urls import build_action_url
from app.core.config import Settings


def build_password_reset_email(
    settings: Settings,
    *,
    to_email: str,
    token: str,
    tenant_id: str,
    tenant_slug: str,
) -> EmailMessage:
    action_url = build_action_url(
        settings,
        template=EmailTemplate.PASSWORD_RESET,
        token=token,
        tenant_slug=tenant_slug,
    )
    subject = "Reset your password"
    text_body = (
        f"You requested a password reset.\n\n"
        f"Open this link to choose a new password (expires in 1 hour):\n{action_url}\n\n"
        f"If you did not request this, you can ignore this email."
    )
    html_body = (
        f"<p>You requested a password reset.</p>"
        f"<p><a href=\"{action_url}\">Reset your password</a></p>"
        f"<p>This link expires in 1 hour. If you did not request this, ignore this email.</p>"
    )
    return EmailMessage(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        template=EmailTemplate.PASSWORD_RESET,
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        token=token,
        action_url=action_url,
    )


def build_email_verification_email(
    settings: Settings,
    *,
    to_email: str,
    token: str,
    tenant_id: str,
    tenant_slug: str,
) -> EmailMessage:
    action_url = build_action_url(
        settings,
        template=EmailTemplate.EMAIL_VERIFICATION,
        token=token,
        tenant_slug=tenant_slug,
    )
    subject = "Verify your email address"
    text_body = (
        f"Please verify your email address.\n\n"
        f"Open this link to verify (expires in 24 hours):\n{action_url}\n"
    )
    html_body = (
        f"<p>Please verify your email address.</p>"
        f"<p><a href=\"{action_url}\">Verify email</a></p>"
        f"<p>This link expires in 24 hours.</p>"
    )
    return EmailMessage(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        template=EmailTemplate.EMAIL_VERIFICATION,
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        token=token,
        action_url=action_url,
    )


def build_user_invite_email(
    settings: Settings,
    *,
    to_email: str,
    token: str,
    tenant_id: str,
    tenant_slug: str,
    hospital_name: str,
) -> EmailMessage:
    action_url = build_action_url(
        settings,
        template=EmailTemplate.USER_INVITE,
        token=token,
        tenant_slug=tenant_slug,
    )
    subject = f"You are invited to join {hospital_name}"
    text_body = (
        f"You have been invited to join {hospital_name}.\n\n"
        f"Accept your invitation and set a password (expires in 72 hours):\n{action_url}\n"
    )
    html_body = (
        f"<p>You have been invited to join <strong>{hospital_name}</strong>.</p>"
        f"<p><a href=\"{action_url}\">Accept invitation</a></p>"
        f"<p>This link expires in 72 hours.</p>"
    )
    return EmailMessage(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        template=EmailTemplate.USER_INVITE,
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        token=token,
        action_url=action_url,
    )


def build_welcome_email(
    settings: Settings,
    *,
    to_email: str,
    tenant_slug: str,
    hospital_name: str,
) -> EmailMessage:
    login_url = f"{settings.frontend_base_url.rstrip('/')}/login?tenant={tenant_slug}"
    subject = f"Welcome to {hospital_name}"
    text_body = (
        f"Your hospital account for {hospital_name} is ready.\n\n"
        f"Sign in here: {login_url}\n"
    )
    html_body = (
        f"<p>Your hospital account for <strong>{hospital_name}</strong> is ready.</p>"
        f"<p><a href=\"{login_url}\">Sign in</a></p>"
    )
    return EmailMessage(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        template=EmailTemplate.WELCOME,
        tenant_slug=tenant_slug,
        action_url=login_url,
    )
