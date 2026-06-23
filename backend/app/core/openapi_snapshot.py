"""OpenAPI schema normalization for contract snapshot tests (MVP-057)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = BACKEND_ROOT / "tests" / "snapshots" / "openapi.json"


def normalize_openapi(spec: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical JSON-serializable dict with stable key ordering."""
    return json.loads(json.dumps(spec, sort_keys=True))


def fetch_openapi_schema(client: TestClient, *, openapi_path: str = "/api/v1/openapi.json") -> dict[str, Any]:
    response = client.get(openapi_path)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch OpenAPI schema: HTTP {response.status_code}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("OpenAPI schema response must be a JSON object")
    return payload


def load_openapi_snapshot(path: Path | None = None) -> dict[str, Any]:
    snapshot_file = path or SNAPSHOT_PATH
    return json.loads(snapshot_file.read_text(encoding="utf-8"))


def write_openapi_snapshot(spec: dict[str, Any], path: Path | None = None) -> Path:
    snapshot_file = path or SNAPSHOT_PATH
    snapshot_file.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_openapi(spec)
    snapshot_file.write_text(
        json.dumps(normalized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return snapshot_file


def compare_openapi_schemas(current: dict[str, Any], expected: dict[str, Any]) -> str | None:
    current_text = json.dumps(normalize_openapi(current), indent=2, sort_keys=True)
    expected_text = json.dumps(normalize_openapi(expected), indent=2, sort_keys=True)
    if current_text == expected_text:
        return None

    import difflib

    diff = difflib.unified_diff(
        expected_text.splitlines(),
        current_text.splitlines(),
        fromfile="tests/snapshots/openapi.json",
        tofile="current OpenAPI",
        lineterm="",
    )
    return "\n".join(diff)
