"""Tenant-scoped SaaS payment-method management (Razorpay tokenization)."""

from __future__ import annotations

import hmac
import hashlib
import uuid

from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.domains.platform.repositories.payment_method_repository import PaymentMethodRepository
from app.models.platform.payment_method import PaymentMethod
from app.models.platform.tenant import Tenant
from app.domains.platform.schemas.payment_method import (
    PaymentMethodResponse,
    RazorpayAddPaymentMethodRequest,
)


class PaymentMethodService:
    """CRUD operations for platform.payment_methods scoped to `tenant_id`."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self._repo = PaymentMethodRepository(db, tenant_id)

    def list_payment_methods(
        self,
        *,
        method_type: str | None = None,
        is_default: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PaymentMethodResponse], int]:
        rows, total = self._repo.list(
            method_type=method_type,
            is_default=is_default,
            search=search,
            page=page,
            page_size=page_size,
        )
        return [self._response_from(r) for r in rows], total

    def add_payment_method(
        self,
        payload: RazorpayAddPaymentMethodRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> PaymentMethodResponse:
        self._verify_razorpay_payment(payload)

        # MVP-126 stub: in production, Razorpay would return method + last4/brand via tokenization.
        # Until the adapter is added, infer a conservative `card` token shape.
        method_type = "card"
        gateway = "razorpay"
        gateway_customer_id = f"rzp_cust_{self.tenant_id}"
        gateway_token_id = f"rzp_token_{payload.razorpay_payment_id}"

        if self._repo.count_active() == 0:
            is_default = True
        else:
            # Tokenization flow uses a verification charge; new methods become default by default.
            is_default = True

        # Enforce single default across active methods.
        if is_default:
            self._repo.unset_defaults()

        row = self._repo.create(
            gateway=gateway,
            gateway_customer_id=gateway_customer_id,
            gateway_token_id=gateway_token_id,
            method_type=method_type,
            last_four=None,
            brand=None,
            is_default=is_default,
            expires_at=None,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.commit()
        self.db.refresh(row)

        # Convert tenant from trial -> active when they add the first payment method.
        if self._get_tenant_status() == "trial":
            self._set_tenant_status("active", actor_id=actor_id)
            self.db.commit()

        return self._response_from(row)

    def get_payment_method(self, payment_method_id: uuid.UUID) -> PaymentMethodResponse:
        row = self._repo.get_by_id(payment_method_id)
        if row is None:
            raise NotFoundError("Payment method not found", field="payment_method_id")
        return self._response_from(row)

    def set_default_payment_method(
        self,
        payment_method_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> PaymentMethodResponse:
        row = self._repo.get_by_id(payment_method_id)
        if row is None:
            raise NotFoundError("Payment method not found", field="payment_method_id")

        self._repo.unset_defaults(exclude_id=payment_method_id)
        row.is_default = True
        row.updated_by = actor_id
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return self._response_from(row)

    def remove_payment_method(
        self,
        payment_method_id: uuid.UUID,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> dict:
        row = self._repo.get_by_id(payment_method_id)
        if row is None:
            raise NotFoundError("Payment method not found", field="payment_method_id")

        was_default = bool(row.is_default)
        self._repo.soft_delete(row, deleted_by=actor_id)
        self.db.commit()

        # If no active methods remain, move tenant into past_due so subscription gates kick in.
        if self._repo.count_active() == 0:
            status = self._get_tenant_status()
            if status in {"trial", "active"}:
                self._set_tenant_status("past_due", actor_id=actor_id)
                self.db.commit()
        elif was_default:
            # Choose the most recently created active method as the new default.
            default_row = self._repo.get_default()
            if default_row is not None:
                self._repo.unset_defaults()
                default_row.is_default = True
                default_row.updated_by = actor_id
                self.db.add(default_row)
                self.db.commit()

        return {"deleted": True, "payment_method_id": str(payment_method_id)}

    def _verify_razorpay_payment(self, payload: RazorpayAddPaymentMethodRequest) -> None:
        settings = get_settings()
        secret = (settings.razorpay_key_secret or "").strip()
        # If not configured (local dev/openapi generation), accept payloads to unblock MVP development.
        if not secret:
            return

        # Razorpay signature verification for payment tokenization uses:
        #   HMAC_SHA256(order_id + '|' + payment_id, secret)
        msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
        expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, payload.razorpay_signature):
            raise ValidationError("Invalid Razorpay payment signature", field="razorpay_signature")

    def _response_from(self, row: PaymentMethod) -> PaymentMethodResponse:
        return PaymentMethodResponse(
            id=row.id,
            gateway=row.gateway,  # type: ignore[arg-type]
            gateway_customer_id=row.gateway_customer_id,
            gateway_token_id=row.gateway_token_id,
            method_type=row.method_type,  # type: ignore[arg-type]
            last_four=row.last_four,
            brand=row.brand,
            is_default=row.is_default,
            expires_at=row.expires_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _get_tenant_status(self) -> str:
        tenant = self.db.scalars(select(Tenant).where(Tenant.id == self.tenant_id, Tenant.deleted_at.is_(None))).first()
        if tenant is None:
            # Tenant must exist; but keep error actionable.
            raise NotFoundError("Tenant not found", field="tenant_id")
        return tenant.status

    def _set_tenant_status(self, status: str, *, actor_id: uuid.UUID | None = None) -> None:
        tenant = self.db.scalars(select(Tenant).where(Tenant.id == self.tenant_id, Tenant.deleted_at.is_(None))).first()
        if tenant is None:
            raise NotFoundError("Tenant not found", field="tenant_id")
        tenant.status = status
        tenant.updated_by = actor_id
        tenant.updated_at = datetime.now(UTC)
        self.db.add(tenant)

