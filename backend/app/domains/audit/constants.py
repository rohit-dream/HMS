"""Audit domain constants."""

from __future__ import annotations

ENTITY_TYPE_AUTH = "auth"
ENTITY_TYPE_USER = "user"

ACTION_LOGIN = "login"
ACTION_LOGOUT = "logout"
ACTION_UPDATE = "update"

OUTCOME_SUCCESS = "success"
OUTCOME_FAILED = "failed"
OUTCOME_LOCKOUT = "lockout"
OUTCOME_PASSWORD_RESET = "password_reset"
