"""Standard API response envelope per API_DESIGN.md §2.3."""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ResponseMeta(BaseModel):
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    tenant_id: str | None = None
    pagination: PaginationMeta | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class APIResponse(BaseModel, Generic[T]):
    data: T | None = None
    meta: ResponseMeta
    errors: list[ErrorDetail] | None = None


def build_meta(request_id: str, tenant_id: UUID | str | None = None) -> ResponseMeta:
    """Build response metadata."""
    tenant_str = str(tenant_id) if tenant_id is not None else None
    return ResponseMeta(request_id=request_id, tenant_id=tenant_str)


def success_response(
    data: Any,
    request_id: str,
    tenant_id: UUID | str | None = None,
) -> dict[str, Any]:
    """Build a success envelope dict for JSONResponse."""
    return APIResponse(
        data=data,
        meta=build_meta(request_id, tenant_id),
        errors=None,
    ).model_dump(mode="json")


def error_response(
    errors: list[ErrorDetail],
    request_id: str,
    tenant_id: UUID | str | None = None,
) -> dict[str, Any]:
    """Build an error envelope dict for JSONResponse."""
    return APIResponse(
        data=None,
        meta=build_meta(request_id, tenant_id),
        errors=errors,
    ).model_dump(mode="json")
