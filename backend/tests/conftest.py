"""Pytest configuration and shared fixtures."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SKIP_STARTUP_CHECKS", "true")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.core.config import get_settings
from app.core.security import clear_key_cache
from app.main import create_app

_KEYS_DIR = Path(__file__).resolve().parents[1] / "keys"
_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _run_alembic_upgrade() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"alembic upgrade head failed:\n{result.stderr or result.stdout}")


@pytest.fixture(scope="session", autouse=True)
def ensure_database_migrations() -> None:
    """Apply Alembic migrations before integration tests (session-scoped)."""
    _run_alembic_upgrade()


def _ensure_test_jwt_keys() -> tuple[str, str]:
    _KEYS_DIR.mkdir(parents=True, exist_ok=True)
    private_path = _KEYS_DIR / "private.pem"
    public_path = _KEYS_DIR / "public.pem"
    if not private_path.exists():
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_path.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        public_path.write_bytes(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    clear_key_cache()
    return str(private_path), str(public_path)


@pytest.fixture(scope="session")
def settings():
    get_settings.cache_clear()
    private_path, public_path = _ensure_test_jwt_keys()
    os.environ["JWT_PRIVATE_KEY_PATH"] = private_path
    os.environ["JWT_PUBLIC_KEY_PATH"] = public_path
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture(scope="module")
def client(settings):
    settings.skip_startup_checks = True
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
