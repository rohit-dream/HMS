"""Audit write service for security-sensitive and data-mutation events."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from starlette.requests import Request

from app.domains.audit.constants import (
    ACTION_CREATE,
    ACTION_DELETE,
    ACTION_EXPORT,
    ACTION_LOGIN,
    ACTION_LOGOUT,
    ACTION_UPDATE,
    ACTION_VIEW,
    ENTITY_TYPE_AUTH,
    ENTITY_TYPE_OPD_VISIT,
    ENTITY_TYPE_PATIENT,
    ENTITY_TYPE_USER,
    OUTCOME_FAILED,
    OUTCOME_LOCKOUT,
    OUTCOME_PASSWORD_RESET,
    OUTCOME_SUCCESS,
    VALID_AUDIT_ACTIONS,
)
from app.domains.audit.repositories.audit_log_repository import AuditLogRepository
from app.domains.audit.sanitize import sanitize_audit_values
from app.models.audit.audit_log import AuditLog


class AuditService:
    """Tenant-scoped audit writer — callable from any domain service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record_create(
        self,
        *,
        tenant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        new_values: dict | None = None,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
        audit_metadata: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        return self.record_mutation(
            tenant_id=tenant_id,
            action=ACTION_CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=new_values,
            user_id=user_id,
            request=request,
            audit_metadata=audit_metadata,
            created_by=created_by or user_id,
        )

    def record_update(
        self,
        *,
        tenant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        old_values: dict | None = None,
        new_values: dict | None = None,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
        audit_metadata: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        return self.record_mutation(
            tenant_id=tenant_id,
            action=ACTION_UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            request=request,
            audit_metadata=audit_metadata,
            created_by=created_by or user_id,
        )

    def record_delete(
        self,
        *,
        tenant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        old_values: dict | None = None,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
        audit_metadata: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        return self.record_mutation(
            tenant_id=tenant_id,
            action=ACTION_DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            user_id=user_id,
            request=request,
            audit_metadata=audit_metadata,
            created_by=created_by or user_id,
        )

    def record_view(
        self,
        *,
        tenant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
        audit_metadata: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        return self.record_mutation(
            tenant_id=tenant_id,
            action=ACTION_VIEW,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            request=request,
            audit_metadata=audit_metadata,
            created_by=created_by or user_id,
        )

    def record_phi_access(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
    ) -> AuditLog:
        """Log PHI read access (audit.audit_logs until phi_access_logs in S11)."""
        metadata: dict[str, object] = {"phi_access": True}
        if resource_type is not None:
            metadata["resource_type"] = resource_type
        if resource_id is not None:
            metadata["resource_id"] = str(resource_id)
        return self.record_view(
            tenant_id=tenant_id,
            entity_type=ENTITY_TYPE_PATIENT,
            entity_id=patient_id,
            user_id=user_id,
            request=request,
            audit_metadata=metadata,
            created_by=user_id,
        )

    def record_opd_visit_phi_access(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        visit_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
    ) -> AuditLog:
        """Log PHI read when an OPD visit (consultation) is viewed."""
        return self.record_phi_access(
            tenant_id=tenant_id,
            patient_id=patient_id,
            user_id=user_id,
            request=request,
            resource_type=ENTITY_TYPE_OPD_VISIT,
            resource_id=visit_id,
        )

    def record_export(
        self,
        *,
        tenant_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        request: Request | None = None,
        audit_metadata: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        return self.record_mutation(
            tenant_id=tenant_id,
            action=ACTION_EXPORT,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            request=request,
            audit_metadata=audit_metadata,
            created_by=created_by or user_id,
        )

    def record_mutation(
        self,
        *,
        tenant_id: uuid.UUID,
        action: str,
        entity_type: str,
        user_id: uuid.UUID | None = None,
        entity_id: uuid.UUID | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        audit_metadata: dict | None = None,
        request: Request | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        if action not in VALID_AUDIT_ACTIONS:
            raise ValueError(f"Invalid audit action: {action}")

        return self._record(
            tenant_id=tenant_id,
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            entity_id=entity_id,
            old_values=sanitize_audit_values(old_values),
            new_values=sanitize_audit_values(new_values),
            audit_metadata=sanitize_audit_values(audit_metadata),
            request=request,
            created_by=created_by,
        )

    def record_login_success(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        request: Request | None = None,
    ) -> AuditLog:
        return self._record(
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
    ) -> AuditLog:
        metadata: dict[str, str | int] = {"outcome": OUTCOME_FAILED}
        if attempts is not None:
            metadata["attempts"] = attempts
        return self._record(
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
    ) -> AuditLog:
        metadata: dict[str, str | int] = {"outcome": OUTCOME_LOCKOUT}
        if attempts is not None:
            metadata["attempts"] = attempts
        return self._record(
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
    ) -> AuditLog:
        return self._record(
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
    ) -> AuditLog:
        return self._record(
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
        old_values: dict | None = None,
        new_values: dict | None = None,
        audit_metadata: dict | None = None,
        request: Request | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        request_id, ip_address, user_agent = _request_audit_fields(request)
        return AuditLogRepository(self.db, tenant_id).create(
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
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
