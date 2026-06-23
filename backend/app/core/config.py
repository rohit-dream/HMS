"""Pydantic settings — single source of configuration from environment."""

from functools import lru_cache
from typing import Literal, Self
from urllib.parse import quote_plus

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import API_V1_PREFIX, APP_NAME, APP_VERSION


class Settings(BaseSettings):
    """Application settings loaded from environment and optional `.env.local`."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: str = "INFO"
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    api_v1_prefix: str = API_V1_PREFIX

    # Database — use DATABASE_URL or individual DATABASE_* variables
    database_url: str | None = Field(default=None, description="Full PostgreSQL URL")
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "hms_dev"
    database_user: str = "hms"
    database_password: str = "hms"
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_echo: bool = False
    database_connect_timeout_seconds: int = Field(default=3, ge=1, le=30)

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_connect_timeout_seconds: int = Field(default=2, ge=1, le=30)

    # CORS
    cors_origins: str = "http://localhost:5173"

    # JWT (RS256)
    jwt_private_key_path: str = "./keys/private.pem"
    jwt_public_key_path: str = "./keys/public.pem"
    jwt_access_token_expire_minutes: int = 30
    jwt_issuer: str = "https://auth.platform.com"
    jwt_refresh_token_expire_days: int = 7
    tenant_base_domain: str = "platform.com"
    auth_rate_limit_per_minute: int = Field(default=10, ge=1, le=1000)

    # CAPTCHA (hCaptcha)
    captcha_bypass: bool = False
    hcaptcha_secret_key: str = ""
    captcha_verify_timeout_seconds: int = Field(default=5, ge=1, le=30)

    # AWS placeholders
    aws_region: str = "ap-south-1"
    s3_bucket: str = "hms-dev-files"
    sqs_queue_url: str = ""
    ses_from_email: str = "noreply@platform.com"
    email_provider: Literal["log", "ses"] = "log"
    frontend_base_url: str = "http://localhost:5173"

    # Startup validation
    skip_startup_checks: bool = False

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def assemble_database_url(self) -> Self:
        if not self.database_url:
            password = quote_plus(self.database_password)
            self.database_url = (
                f"postgresql://{self.database_user}:{password}"
                f"@{self.database_host}:{self.database_port}/{self.database_name}"
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
