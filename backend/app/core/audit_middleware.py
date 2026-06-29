"""HTTP mutation audit middleware — logs successful POST/PUT/PATCH/DELETE (MVP-054)."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.database import session_scope, set_rls_tenant_context, use_rls_enforced_role
from app.domains.audit.constants import ACTION_CREATE, ACTION_DELETE, ACTION_UPDATE
from app.domains.audit.services.audit_service import AuditService

logger = logging.getLogger(__name__)

MUTATION_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Auth and health routes already emit dedicated audit rows or are non-mutating.
AUDIT_SKIP_PATH_SUFFIXES = (
    "/auth/login",
    "/auth/logout",
    "/auth/refresh",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/change-password",
    "/health",
    "/health/ready",
)

MAX_AUDIT_BODY_BYTES = 65_536


def method_to_audit_action(method: str) -> str:
    normalized = method.upper()
    if normalized == "POST":
        return ACTION_CREATE
    if normalized in {"PUT", "PATCH"}:
        return ACTION_UPDATE
    if normalized == "DELETE":
        return ACTION_DELETE
    raise ValueError(f"Unsupported mutation method: {method}")


def is_mutation_method(method: str) -> bool:
    return method.upper() in MUTATION_METHODS


def should_skip_audit_path(path: str, api_prefix: str) -> bool:
    if not path.startswith(api_prefix):
        return True
    relative = path[len(api_prefix) :]
    return any(
        relative == suffix or relative.startswith(f"{suffix}/") for suffix in AUDIT_SKIP_PATH_SUFFIXES
    )


def resolve_audit_resource(path: str, api_prefix: str) -> tuple[str, uuid.UUID | None]:
    """Derive entity_type and optional entity_id from the request path."""
    if not path.startswith(api_prefix):
        return "unknown", None

    segments = [segment for segment in path[len(api_prefix) :].strip("/").split("/") if segment]
    if not segments:
        return "api", None

    entity_id: uuid.UUID | None = None
    resource_segments: list[str] = []
    for segment in segments:
        try:
            entity_id = uuid.UUID(segment)
        except ValueError:
            resource_segments.append(segment)

    entity_type = resource_segments[-1] if resource_segments else "api"
    return entity_type, entity_id


def parse_json_dict(body: bytes) -> dict | None:
    if not body:
        return None
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def extract_entity_id_from_response(body: bytes) -> uuid.UUID | None:
    payload = parse_json_dict(body)
    if not payload:
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    raw_id = data.get("id")
    if not raw_id:
        return None
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        return None


def should_record_mutation_audit(
    *,
    request: Request,
    status_code: int,
    api_prefix: str,
) -> bool:
    if not is_mutation_method(request.method):
        return False
    if should_skip_audit_path(request.url.path, api_prefix):
        return False
    if status_code < 200 or status_code >= 300:
        return False
    if not getattr(request.state, "tenant_id", None):
        return False
    return True


def record_mutation_audit(
    *,
    request: Request,
    status_code: int,
    response_body: bytes,
    request_body: bytes,
    settings: Settings,
) -> None:
    tenant_id = uuid.UUID(str(request.state.tenant_id))
    user_id_raw = getattr(request.state, "user_id", None)
    user_id = uuid.UUID(str(user_id_raw)) if user_id_raw else None

    entity_type, entity_id = resolve_audit_resource(request.url.path, settings.api_v1_prefix)
    if entity_id is None:
        entity_id = extract_entity_id_from_response(response_body)

    action = method_to_audit_action(request.method)
    new_values = None
    if request.method.upper() in {"POST", "PUT", "PATCH"}:
        new_values = parse_json_dict(request_body)

    audit_metadata = {
        "http_method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "source": "mutation_middleware",
    }

    with session_scope(settings) as db:
        use_rls_enforced_role(db)
        set_rls_tenant_context(db, tenant_id)
        AuditService(db).record_mutation(
            tenant_id=tenant_id,
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            entity_id=entity_id,
            new_values=new_values,
            request=request,
            audit_metadata=audit_metadata,
            created_by=user_id,
        )


async def capture_response_body(response: Response) -> tuple[Response, bytes]:
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    return (
        Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        ),
        body,
    )


def create_mutation_audit_middleware(
    settings: Settings,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    async def mutation_audit_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_body = b""
        if (
            is_mutation_method(request.method)
            and not should_skip_audit_path(request.url.path, settings.api_v1_prefix)
            and request.headers.get("content-type", "").startswith("application/json")
        ):
            request_body = await request.body()
            if len(request_body) > MAX_AUDIT_BODY_BYTES:
                request_body = b""

            async def receive() -> dict:
                return {"type": "http.request", "body": request_body, "more_body": False}

            request = Request(request.scope, receive)

        response = await call_next(request)

        if not should_record_mutation_audit(
            request=request,
            status_code=response.status_code,
            api_prefix=settings.api_v1_prefix,
        ):
            return response

        try:
            response, response_body = await capture_response_body(response)
            record_mutation_audit(
                request=request,
                status_code=response.status_code,
                response_body=response_body,
                request_body=request_body,
                settings=settings,
            )
        except Exception:
            logger.exception("mutation audit middleware failed for %s %s", request.method, request.url.path)

        return response

    return mutation_audit_middleware
