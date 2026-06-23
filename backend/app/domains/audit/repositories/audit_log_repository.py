"""Persistence for audit.audit_logs."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def create(
        self,
        *,
        action: str,
        entity_type: str,
        user_id: uuid.UUID | None = None,
        entity_id: uuid.UUID | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: uuid.UUID | None = None,
        audit_metadata: dict | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AuditLog:
        row = AuditLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            audit_metadata=audit_metadata,
            created_by=created_by,
        )
        self.db.add(row)
        return row
