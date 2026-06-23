"""Audit write service for security-sensitive events."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from starlette.requests import Request

from app.domains.audit.constants import (
    ACTION_LOGIN,
    ACTION_LOGOUT,
    ACTION_UPDATE,
    ENTITY_TYPE_AUTH,
    ENTITY_TYPE_USER,
    OUTCOME_FAILED,
    OUTCOME_LOCKOUT,
    OUTCOME_PASSWORD_RESET,
    OUTCOME_SUCCESS,
)
from app.domains.audit.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_login_success(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        self._record(
            tenant_id=tenant_id,
            action=ACTION_LOGIN,
            entity_type=ENTITY_TYPE_USER,
            user_id=user_id,
            entity_id=user_id,
            audit_metadata={"outcome": OUTCOME_SUCCESS},
            request=request,
            created_by=user_id,
        )

    def record_login_failed(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None,
        request: Request | None = None,
        attempts: int | None = None,
    ) -> None:
        metadata: dict[str, str | int] = {"outcome": OUTCOME_FAILED}
        if attempts is not None:
            metadata["attempts"] = attempts
        self._record(
            tenant_id=tenant_id,
            action=ACTION_LOGIN,
            entity_type=ENTITY_TYPE_AUTH,
            user_id=user_id,
            entity_id=user_id,
            audit_metadata=metadata,
            request=request,
            created_by=user_id,
        )

    def record_account_lockout(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        request: Request | None = None,
        attempts: int | None = None,
    ) -> None:
        metadata: dict[str, str | int] = {"outcome": OUTCOME_LOCKOUT}
        if attempts is not None:
            metadata["attempts"] = attempts
        self._record(
            tenant_id=tenant_id,
            action=ACTION_LOGIN,
            entity_type=ENTITY_TYPE_USER,
            user_id=user_id,
            entity_id=user_id,
            audit_metadata=metadata,
            request=request,
            created_by=user_id,
        )

    def record_logout(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        self._record(
            tenant_id=tenant_id,
            action=ACTION_LOGOUT,
            entity_type=ENTITY_TYPE_USER,
            user_id=user_id,
            entity_id=user_id,
            request=request,
            created_by=user_id,
        )

    def record_password_reset(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        self._record(
            tenant_id=tenant_id,
            action=ACTION_UPDATE,
            entity_type=ENTITY_TYPE_USER,
            user_id=user_id,
            entity_id=user_id,
            audit_metadata={"event": OUTCOME_PASSWORD_RESET},
            request=request,
            created_by=user_id,
        )

    def _record(
        self,
        *,
        tenant_id: uuid.UUID,
        action: str,
        entity_type: str,
        user_id: uuid.UUID | None = None,
        entity_id: uuid.UUID | None = None,
        audit_metadata: dict | None = None,
        request: Request | None = None,
        created_by: uuid.UUID | None = None,
    ) -> None:
        request_id, ip_address, user_agent = _request_audit_fields(request)
        AuditLogRepository(self.db, tenant_id).create(
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            audit_metadata=audit_metadata,
            created_by=created_by,
        )


def _request_audit_fields(request: Request | None) -> tuple[uuid.UUID | None, str | None, str | None]:
    if request is None:
        return None, None, None

    request_id_raw = getattr(request.state, "request_id", None)
    request_id = uuid.UUID(request_id_raw) if request_id_raw else None

    ip_address = None
    if request.client and request.client.host:
        try:
            import ipaddress

            ipaddress.ip_address(request.client.host)
            ip_address = request.client.host
        except ValueError:
            ip_address = None

    return request_id, ip_address, request.headers.get("user-agent")
