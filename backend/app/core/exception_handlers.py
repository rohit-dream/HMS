"""Map exceptions to standard API error envelope."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AccountLockedError,
    AppError,
    ConflictError,
    FeatureNotImplementedError,
    ForbiddenError,
    NotFoundError,
    PlanLimitError,
    RateLimitExceededError,
    TenantSuspendedError,
    UnauthorizedError,
)
from app.core.logging import get_logger
from app.core.response import ErrorDetail, error_response

logger = get_logger(__name__)

_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    ConflictError: 409,
    PlanLimitError: 402,
    AccountLockedError: 423,
    TenantSuspendedError: 403,
    RateLimitExceededError: 429,
    FeatureNotImplementedError: 501,
}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        status = 422 if exc.code == "validation_error" else _STATUS_MAP.get(type(exc), 400)
        body = error_response(
            [ErrorDetail(code=exc.code, message=exc.message, field=exc.field)],
            _request_id(request),
            getattr(request.state, "tenant_id", None),
        )
        return JSONResponse(status_code=status, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            ErrorDetail(
                code="validation_error",
                message=err.get("msg", "Validation error"),
                field=".".join(str(loc) for loc in err.get("loc", []) if loc != "body") or None,
            )
            for err in exc.errors()
        ]
        body = error_response(errors, _request_id(request))
        return JSONResponse(status_code=422, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        body = error_response(
            [ErrorDetail(code="http_error", message=str(exc.detail))],
            _request_id(request),
        )
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        body = error_response(
            [ErrorDetail(code="internal_error", message="An unexpected error occurred")],
            _request_id(request),
        )
        return JSONResponse(status_code=500, content=body)
