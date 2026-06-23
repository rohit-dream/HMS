"""Identity domain constants."""

from __future__ import annotations

MAX_HOSPITAL_OWNERS_PER_TENANT = 2
HOSPITAL_OWNER_ROLE = "hospital_owner"
PLATFORM_ADMIN_ROLE = "platform_admin"
PASSWORD_RESET_TOKEN_HOURS = 1
EMAIL_VERIFICATION_TOKEN_HOURS = 24
USER_INVITE_TOKEN_HOURS = 72
FORGOT_PASSWORD_MESSAGE = "If the email exists, a reset link has been sent."
RESET_PASSWORD_SUCCESS_MESSAGE = "Password updated successfully."
EMAIL_VERIFICATION_SUCCESS_MESSAGE = "Email verified successfully."
EMAIL_ALREADY_VERIFIED_MESSAGE = "Email is already verified."
RESEND_VERIFICATION_MESSAGE = "Verification email sent."
