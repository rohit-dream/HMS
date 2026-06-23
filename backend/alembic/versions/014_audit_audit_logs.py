"""audit.audit_logs — immutable security audit trail (MVP-033).

Revision ID: 014_audit_audit_logs
Revises: 013_email_verification_tokens
"""

from collections.abc import Sequence

from alembic import op

from app.db.rls_policies import (
    disable_rls_statements,
    enable_rls_statements,
    tenant_isolation_policy_statements,
)

revision: str = "014_audit_audit_logs"
down_revision: str | None = "013_email_verification_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "audit"
_TABLE = "audit_logs"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE {_SCHEMA}.{_TABLE} (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            user_id         UUID,
            action          VARCHAR(50) NOT NULL
                            CHECK (action IN (
                                'create', 'update', 'delete',
                                'login', 'logout', 'export', 'view'
                            )),
            entity_type     VARCHAR(50) NOT NULL,
            entity_id       UUID,
            old_values      JSONB,
            new_values      JSONB,
            ip_address      INET,
            user_agent      TEXT,
            request_id      UUID,
            metadata        JSONB,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID
        )
        """
    )
    op.execute(
        f"COMMENT ON TABLE {_SCHEMA}.{_TABLE} IS "
        "'Immutable security and data mutation audit trail.'"
    )
    op.execute(
        f"CREATE UNIQUE INDEX uq_{_TABLE}_tenant_id_id ON {_SCHEMA}.{_TABLE} (tenant_id, id)"
    )
    op.execute(
        f"""
        ALTER TABLE {_SCHEMA}.{_TABLE}
            ADD CONSTRAINT fk_{_TABLE}_user
            FOREIGN KEY (tenant_id, user_id)
            REFERENCES core.users (tenant_id, id)
        """
    )
    op.execute(
        f"CREATE INDEX idx_{_TABLE}_tenant_entity "
        f"ON {_SCHEMA}.{_TABLE} (tenant_id, entity_type, entity_id)"
    )
    op.execute(
        f"CREATE INDEX idx_{_TABLE}_tenant_user "
        f"ON {_SCHEMA}.{_TABLE} (tenant_id, user_id, created_at)"
    )
    op.execute(
        f"CREATE INDEX idx_{_TABLE}_created_brin "
        f"ON {_SCHEMA}.{_TABLE} USING BRIN (created_at)"
    )
    op.execute(
        f"CREATE INDEX idx_{_TABLE}_tenant_id ON {_SCHEMA}.{_TABLE} (tenant_id)"
    )

    for stmt in enable_rls_statements(_SCHEMA, _TABLE):
        op.execute(stmt)
    for stmt in tenant_isolation_policy_statements(_SCHEMA, _TABLE):
        op.execute(stmt)

    op.execute("GRANT USAGE ON SCHEMA audit TO hms_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO hms_app"
    )


def downgrade() -> None:
    for stmt in disable_rls_statements(_SCHEMA, _TABLE):
        op.execute(stmt)
    op.execute(f"DROP TABLE IF EXISTS {_SCHEMA}.{_TABLE} CASCADE")
