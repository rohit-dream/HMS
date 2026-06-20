"""RBAC tables — roles, permissions, role_permissions, user_roles.

Revision ID: 003_rbac_tables
Revises: 002_auth_tables
"""

from collections.abc import Sequence

from alembic import op

revision: str = "003_rbac_tables"
down_revision: str | None = "002_auth_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE core.roles (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            name            VARCHAR(100) NOT NULL,
            code            VARCHAR(50) NOT NULL,
            description     TEXT,
            is_system       BOOLEAN NOT NULL DEFAULT FALSE,
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_roles_tenant_id_id ON core.roles (tenant_id, id)")
    op.execute("CREATE UNIQUE INDEX uq_roles_tenant_code ON core.roles (tenant_id, code)")
    op.execute("CREATE INDEX idx_roles_tenant_id ON core.roles (tenant_id)")
    op.execute(
        """
        CREATE TRIGGER trg_roles_updated_at BEFORE UPDATE ON core.roles
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE core.permissions (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            code            VARCHAR(100) NOT NULL,
            name            VARCHAR(150) NOT NULL,
            module          VARCHAR(50) NOT NULL,
            description     TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_permissions_tenant_id_id ON core.permissions (tenant_id, id)")
    op.execute("CREATE UNIQUE INDEX uq_permissions_tenant_code ON core.permissions (tenant_id, code)")
    op.execute("CREATE INDEX idx_permissions_tenant_id ON core.permissions (tenant_id)")
    op.execute(
        """
        CREATE TRIGGER trg_permissions_updated_at BEFORE UPDATE ON core.permissions
            FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE TABLE core.role_permissions (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            role_id         UUID NOT NULL,
            permission_id   UUID NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_role_permissions_tenant_id_id ON core.role_permissions (tenant_id, id)")
    op.execute(
        """
        ALTER TABLE core.role_permissions
            ADD CONSTRAINT fk_role_permissions_role FOREIGN KEY (tenant_id, role_id)
            REFERENCES core.roles (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        ALTER TABLE core.role_permissions
            ADD CONSTRAINT fk_role_permissions_perm FOREIGN KEY (tenant_id, permission_id)
            REFERENCES core.permissions (tenant_id, id)
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_role_permissions ON core.role_permissions (tenant_id, role_id, permission_id)"
    )

    op.execute(
        """
        CREATE TABLE core.user_roles (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NOT NULL REFERENCES platform.tenants(id),
            user_id         UUID NOT NULL,
            role_id         UUID NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID,
            updated_at      TIMESTAMPTZ,
            updated_by      UUID,
            deleted_at      TIMESTAMPTZ,
            deleted_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_user_roles_tenant_id_id ON core.user_roles (tenant_id, id)")
    op.execute(
        """
        ALTER TABLE core.user_roles
            ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (tenant_id, user_id)
            REFERENCES core.users (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        ALTER TABLE core.user_roles
            ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (tenant_id, role_id)
            REFERENCES core.roles (tenant_id, id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE UNIQUE INDEX uq_user_roles ON core.user_roles (tenant_id, user_id, role_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS core.user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS core.role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS core.permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS core.roles CASCADE")
