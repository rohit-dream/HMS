"""Integration test — Alembic foundation migration against PostgreSQL."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_alembic_foundation_migration_applies() -> None:
    """Run upgrade head and verify schemas + functions exist."""
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    with engine.connect() as conn:
        schemas = conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('platform', 'core', 'audit')"
            )
        ).fetchall()
        assert len(schemas) == 3

        ext = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto'")
        ).fetchone()
        assert ext is not None

        fn = conn.execute(
            text(
                "SELECT 1 FROM pg_proc p "
                "JOIN pg_namespace n ON p.pronamespace = n.oid "
                "WHERE n.nspname = 'public' AND p.proname = 'set_updated_at'"
            )
        ).fetchone()
        assert fn is not None

    engine.dispose()
