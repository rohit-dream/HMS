"""OpenAPI contract snapshot test (MVP-057)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.openapi_snapshot import (
    SNAPSHOT_PATH,
    compare_openapi_schemas,
    fetch_openapi_schema,
    load_openapi_snapshot,
)


def test_openapi_schema_matches_snapshot(client: TestClient) -> None:
    """CI gate — undocumented OpenAPI changes fail until snapshot is updated."""
    assert SNAPSHOT_PATH.is_file(), (
        f"Missing OpenAPI snapshot at {SNAPSHOT_PATH}. "
        "Run: python scripts/update_openapi_snapshot.py"
    )

    current = fetch_openapi_schema(client)
    expected = load_openapi_snapshot()
    diff = compare_openapi_schemas(current, expected)
    if diff:
        pytest.fail(
            "OpenAPI schema differs from committed snapshot.\n"
            "If the API change is intentional, run:\n"
            "  python scripts/update_openapi_snapshot.py\n\n"
            f"{diff}"
        )


def test_openapi_snapshot_covers_core_modules(client: TestClient) -> None:
    """Guardrail — snapshot must include auth, hospital, admin, patients, and OPD modules."""
    spec = fetch_openapi_schema(client)
    paths = spec.get("paths", {})
    required_prefixes = (
        "/api/v1/auth/login",
        "/api/v1/hospital/profile",
        "/api/v1/admin/users",
        "/api/v1/patients",
        "/api/v1/opd/visits",
    )
    missing = [prefix for prefix in required_prefixes if prefix not in paths]
    assert not missing, f"OpenAPI missing expected paths: {missing}"
