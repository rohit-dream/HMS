#!/usr/bin/env python3
"""Regenerate committed OpenAPI contract snapshot (MVP-057)."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.core.jwt_keygen import ensure_jwt_keys
from app.core.openapi_snapshot import fetch_openapi_schema, write_openapi_snapshot
from app.core.security import clear_key_cache
from app.main import create_app


def main() -> int:
    keys_dir = BACKEND_ROOT / "keys"
    private_path, public_path = ensure_jwt_keys(keys_dir)
    clear_key_cache()
    get_settings.cache_clear()

    import os

    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("SKIP_STARTUP_CHECKS", "true")
    os.environ["JWT_PRIVATE_KEY_PATH"] = str(private_path)
    os.environ["JWT_PUBLIC_KEY_PATH"] = str(public_path)

    get_settings.cache_clear()
    settings = get_settings()
    settings.skip_startup_checks = True

    app = create_app(settings)
    with TestClient(app) as client:
        schema = fetch_openapi_schema(client)

    snapshot_path = write_openapi_snapshot(schema)
    print(f"OpenAPI snapshot updated: {snapshot_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
