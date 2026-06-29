"""Audit domain constants."""

from __future__ import annotations

ENTITY_TYPE_AUTH = "auth"
ENTITY_TYPE_USER = "user"
ENTITY_TYPE_PATIENT = "patient"
ENTITY_TYPE_OPD_VISIT = "opd_visit"

ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_LOGIN = "login"
ACTION_LOGOUT = "logout"
ACTION_EXPORT = "export"
ACTION_VIEW = "view"

VALID_AUDIT_ACTIONS = frozenset(
    {
        ACTION_CREATE,
        ACTION_UPDATE,
        ACTION_DELETE,
        ACTION_LOGIN,
        ACTION_LOGOUT,
        ACTION_EXPORT,
        ACTION_VIEW,
    }
)

OUTCOME_SUCCESS = "success"
OUTCOME_FAILED = "failed"
OUTCOME_LOCKOUT = "lockout"
OUTCOME_PASSWORD_RESET = "password_reset"
