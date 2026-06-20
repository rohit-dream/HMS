"""Health probe endpoints."""

import asyncio

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.response import success_response
from app.core.startup import run_connectivity_checks

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness(request: Request) -> dict:
    """Liveness probe — process is running."""
    settings = get_settings()
    return success_response(
        data={
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
        request_id=request.state.request_id,
    )


@router.get("/health/ready")
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe — database and Redis connectivity."""
    settings = get_settings()
    db_ok, redis_ok = await asyncio.to_thread(run_connectivity_checks, settings)
    healthy = db_ok and redis_ok

    body = success_response(
        data={
            "status": "ready" if healthy else "not_ready",
            "checks": {
                "database": "ok" if db_ok else "failed",
                "redis": "ok" if redis_ok else "failed",
            },
        },
        request_id=request.state.request_id,
    )
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=body)
