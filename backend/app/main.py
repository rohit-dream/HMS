"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import dispose_engine
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import register_middleware
from app.core.startup import run_startup_validation_async

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    settings: Settings = app.state.settings

    if not settings.skip_startup_checks:
        result = await run_startup_validation_async(settings)
        if not result.ok and not settings.is_development:
            raise RuntimeError(f"Startup validation failed: {result.errors}")
        if result.warnings:
            for warning in result.warnings:
                logger.warning("Startup warning: %s", warning)

    logger.info("Application started — environment=%s", settings.environment)
    yield
    dispose_engine()
    logger.info("Application shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Hospital Management SaaS API",
        version=settings.app_version,
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    register_exception_handlers(app)
    register_middleware(app, settings)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        """Help developers who open http://localhost:8000/ directly."""
        prefix = settings.api_v1_prefix
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "message": "API is running. Use the versioned prefix below.",
            "links": {
                "health": f"{prefix}/health",
                "ready": f"{prefix}/health/ready",
                "docs": f"{prefix}/docs",
            },
        }

    return app


app = create_app()
