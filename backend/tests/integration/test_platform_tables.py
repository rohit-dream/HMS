"""Integration tests — MVP-011 platform schema tables."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]

PLATFORM_TABLES: tuple[str, ...] = (
    "tenants",
    "subscription_plans",
    "tenant_subscriptions",
    "tenant_locations",
    "tenant_settings",
)

REQUIRED_TENANT_COLUMNS: frozenset[str] = frozenset(
    {
        "id",
        "tenant_id",
        "name",
        "slug",
        "status",
        "email",
        "created_at",
        "version",
    }
)

REQUIRED_PLAN_COLUMNS: frozenset[str] = frozenset(
    {
        "tenant_id",
        "code",
        "name",
        "price_monthly",
        "max_users",
        "features",
        "is_active",
    }
)

REQUIRED_SUBSCRIPTION_COLUMNS: frozenset[str] = frozenset(
    {
        "tenant_id",
        "plan_id",
        "status",
        "billing_cycle",
        "current_period_start",
        "current_period_end",
    }
)


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _table_columns(conn, schema: str, table: str) -> set[str]:
    rows = conn.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            """
        ),
        {"schema": schema, "table": table},
    ).fetchall()
    return {row[0] for row in rows}


@pytest.mark.integration
def test_all_platform_tables_exist() -> None:
    """All five MVP platform tables must exist after alembic upgrade head."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            for table in PLATFORM_TABLES:
                exists = conn.execute(
                    text(
                        """
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'platform' AND table_name = :table
                        """
                    ),
                    {"table": table},
                ).fetchone()
                assert exists is not None, f"platform.{table} is missing"
    finally:
        engine.dispose()


@pytest.mark.integration
def test_subscription_tables_have_required_columns() -> None:
    """subscription_plans and tenant_subscriptions match DATABASE_DESIGN.md."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            tenant_cols = _table_columns(conn, "platform", "tenants")
            assert REQUIRED_TENANT_COLUMNS.issubset(tenant_cols)

            plan_cols = _table_columns(conn, "platform", "subscription_plans")
            assert REQUIRED_PLAN_COLUMNS.issubset(plan_cols)

            sub_cols = _table_columns(conn, "platform", "tenant_subscriptions")
            assert REQUIRED_SUBSCRIPTION_COLUMNS.issubset(sub_cols)
    finally:
        engine.dispose()


@pytest.mark.integration
def test_tenant_subscriptions_references_plans() -> None:
    """plan_id FK must reference subscription_plans(id) for cross-tenant plan assignment."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            fk = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                      ON ccu.constraint_name = tc.constraint_name
                     AND ccu.table_schema = tc.table_schema
                    WHERE tc.table_schema = 'platform'
                      AND tc.table_name = 'tenant_subscriptions'
                      AND tc.constraint_type = 'FOREIGN KEY'
                      AND kcu.column_name = 'plan_id'
                      AND ccu.table_name = 'subscription_plans'
                    """
                )
            ).fetchone()
            assert fk is not None
    finally:
        engine.dispose()


@pytest.mark.integration
def test_subscription_plans_updated_at_trigger_exists() -> None:
    """Updated_at trigger must be present on subscription_plans."""
    _run_alembic_upgrade()
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            trigger = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_trigger t
                    JOIN pg_class c ON t.tgrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname = 'platform'
                      AND c.relname = 'subscription_plans'
                      AND t.tgname = 'trg_subscription_plans_updated_at'
                      AND NOT t.tgisinternal
                    """
                )
            ).fetchone()
            assert trigger is not None
    finally:
        engine.dispose()
