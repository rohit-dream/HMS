"""Integration tests — generic audit write service (MVP-053)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.core.security import hash_password
from app.domains.audit.constants import ACTION_CREATE, ACTION_UPDATE
from app.domains.audit.sanitize import REDACTED
from app.domains.audit.services.audit_service import AuditService
from app.models.audit.audit_log import AuditLog
from tests.helpers.rbac import provision_tenant_with_role

pytestmark = pytest.mark.integration


def test_audit_service_writes_mutation_to_audit_logs_table() -> None:
    tenant_id = uuid.uuid4()
    email = f"audit-write-{tenant_id.hex[:8]}@example.com"
    slug = f"audit-write-{tenant_id.hex[:8]}"

    with session_scope() as db:
        data = provision_tenant_with_role(
            db,
            slug=slug,
            email=email,
            password_hash=hash_password("SecurePass@123"),
            role_code="hospital_admin",
        )
        db.commit()

    entity_id = uuid.uuid4()
    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data["tenant_id"])
        audit = AuditService(db)
        audit.record_create(
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            entity_type="patient",
            entity_id=entity_id,
            new_values={"name": "Test Patient", "password": "must-not-persist"},
            created_by=data["user_id"],
        )
        audit.record_update(
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            entity_type="patient",
            entity_id=entity_id,
            old_values={"name": "Test Patient"},
            new_values={"name": "Updated Patient", "refresh_token": "jwt"},
            created_by=data["user_id"],
        )
        db.commit()

    with session_scope() as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, data["tenant_id"])
        rows = list(
            db.scalars(
                select(AuditLog)
                .where(
                    AuditLog.tenant_id == data["tenant_id"],
                    AuditLog.entity_id == entity_id,
                )
                .order_by(AuditLog.created_at)
            ).all()
        )

    assert len(rows) == 2
    assert rows[0].action == ACTION_CREATE
    assert rows[0].new_values == {"name": "Test Patient", "password": REDACTED}
    assert rows[1].action == ACTION_UPDATE
    assert rows[1].old_values == {"name": "Test Patient"}
    assert rows[1].new_values == {"name": "Updated Patient", "refresh_token": REDACTED}
    assert rows[0].created_by == data["user_id"]
