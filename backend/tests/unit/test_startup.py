"""Unit tests for startup validation."""

from app.core.config import Settings
from app.core.startup import validate_settings


def test_validate_settings_assembles_database_url_from_components():
    """DATABASE_URL is optional when DATABASE_* component variables are set."""
    settings = Settings.model_validate(
        {
            "environment": "test",
            "database_url": None,
            "database_host": "localhost",
            "database_name": "hms_test",
            "database_user": "hms",
            "database_password": "hms",
            "redis_url": "redis://localhost:6379/0",
        }
    )
    result = validate_settings(settings)
    assert result.ok
    assert settings.database_url.startswith("postgresql://")
