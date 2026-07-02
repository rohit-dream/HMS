"""Tenant-facing subscription APIs (SaaS billing / payment methods)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.deps import pagination_params
from app.api.v1.subscription_deps import get_payment_method_service
from app.core.authorization import AuthorizationContext, require_permission
from app.core.response import paginated_response, success_response
from app.domains.platform.schemas.payment_method import (
    PaymentMethodResponse,
    RazorpayAddPaymentMethodRequest,
)

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("/payment-methods")
def list_payment_methods(
    request: Request,
    pagination: dict[str, int] = Depends(pagination_params),
    method_type: str | None = Query(default=None, description="Filter by payment method type"),
    is_default: bool | None = Query(default=None),
    search: str | None = Query(default=None, description="Search by gateway token/customer/id/brand"),
    ctx: AuthorizationContext = Depends(require_permission("admin:subscription")),
    service=Depends(get_payment_method_service),
) -> dict:
    """List tokenized subscription payment methods — requires admin:subscription."""
    items, total = service.list_payment_methods(
        method_type=method_type,
        is_default=is_default,
        search=search,
        page=pagination["page"],
        page_size=pagination["page_size"],
    )
    return paginated_response(
        data=[item.model_dump(mode="json") for item in items],
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
        page=pagination["page"],
        page_size=pagination["page_size"],
        total_items=total,
    )


@router.post("/payment-methods", status_code=status.HTTP_201_CREATED)
def add_payment_method(
    request: Request,
    payload: RazorpayAddPaymentMethodRequest,
    ctx: AuthorizationContext = Depends(require_permission("admin:subscription")),
    service=Depends(get_payment_method_service),
) -> JSONResponse:
    """Add a payment method (Razorpay tokenization verification) — requires admin:subscription."""
    data: PaymentMethodResponse = service.add_payment_method(payload, actor_id=ctx.user.user_id)
    body = success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=body)


@router.get("/payment-methods/{payment_method_id}")
def get_payment_method(
    request: Request,
    payment_method_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:subscription")),
    service=Depends(get_payment_method_service),
) -> dict:
    """Get a single payment method — requires admin:subscription."""
    data = service.get_payment_method(payment_method_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.delete("/payment-methods/{payment_method_id}")
def remove_payment_method(
    request: Request,
    payment_method_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:subscription")),
    service=Depends(get_payment_method_service),
) -> dict:
    """Remove a payment method — requires admin:subscription."""
    result = service.remove_payment_method(payment_method_id, actor_id=ctx.user.user_id)
    return success_response(
        data=result,
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )


@router.put("/payment-methods/{payment_method_id}/default")
def set_default_payment_method(
    request: Request,
    payment_method_id: uuid.UUID,
    ctx: AuthorizationContext = Depends(require_permission("admin:subscription")),
    service=Depends(get_payment_method_service),
) -> dict:
    """Set a payment method as default — requires admin:subscription."""
    data = service.set_default_payment_method(payment_method_id, actor_id=ctx.user.user_id)
    return success_response(
        data=data.model_dump(mode="json"),
        request_id=request.state.request_id,
        tenant_id=ctx.user.tenant_id,
    )
