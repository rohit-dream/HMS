"""Middleware registration — correlation ID, CORS."""

import uuid
from collections.abc import Callable

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.constants import REQUEST_ID_HEADER, TENANT_ID_HEADER
from app.core.logging import bind_request_context, clear_request_context


def register_middleware(app: FastAPI, settings: Settings) -> None:
    """Register middleware in execution order (first added = outermost)."""

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        tenant_header = request.headers.get(TENANT_ID_HEADER)
        if tenant_header and settings.is_development:
            request.state.tenant_id = tenant_header

        bind_request_context(request_id=request_id, tenant_id=tenant_header)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            clear_request_context()

    @app.middleware("http")
    async def authorization_context_middleware(request: Request, call_next: Callable) -> Response:
        """Initialize authorization state; resolved by get_authorization_context dependency."""
        if not hasattr(request.state, "permissions"):
            request.state.permissions = []
        if not hasattr(request.state, "roles"):
            request.state.roles = []
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
