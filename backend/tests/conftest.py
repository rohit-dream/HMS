"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SKIP_STARTUP_CHECKS", "true")
os.environ.setdefault("DATABASE_URL", "postgresql://hms:hms@localhost:5432/hms_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def settings():
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture(scope="module")
def client():
    get_settings.cache_clear()
    settings = get_settings()
    settings.skip_startup_checks = True
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
