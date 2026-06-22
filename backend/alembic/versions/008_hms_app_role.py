"""Application database role for RLS enforcement (non-superuser).

Revision ID: 008_hms_app_role
Revises: 007_platform_rls
"""

from collections.abc import Sequence

from alembic import op

revision: str = "008_hms_app_role"
down_revision: str | None = "007_platform_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hms_app') THEN
                CREATE ROLE hms_app NOINHERIT LOGIN PASSWORD 'hms';
            END IF;
        END
        $$;
        """
    )
    op.execute("GRANT USAGE ON SCHEMA platform, core, public TO hms_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform TO hms_app"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO hms_app"
    )
    op.execute("GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA platform TO hms_app")
    op.execute("GRANT EXECUTE ON FUNCTION public.set_updated_at() TO hms_app")
    op.execute("GRANT hms_app TO CURRENT_USER")


def downgrade() -> None:
    op.execute("REVOKE hms_app FROM CURRENT_USER")
    op.execute("DROP ROLE IF EXISTS hms_app")
