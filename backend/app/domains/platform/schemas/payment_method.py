"""Pydantic schemas for platform SaaS payment methods (Razorpay tokenization)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PaymentGateway = Literal["razorpay", "stripe"]
PaymentMethodType = Literal["card", "upi", "netbanking"]


class RazorpayAddPaymentMethodRequest(BaseModel):
    """
    Tokenization verification payload from the frontend.

    The frontend initiates Razorpay Checkout and submits these values:
    - razorpay_payment_id
    - razorpay_order_id
    - razorpay_signature
    """

    razorpay_payment_id: str = Field(min_length=1, max_length=255)
    razorpay_order_id: str = Field(min_length=1, max_length=255)
    razorpay_signature: str = Field(min_length=1, max_length=255)


class PaymentMethodResponse(BaseModel):
    id: uuid.UUID
    gateway: PaymentGateway
    gateway_customer_id: str
    gateway_token_id: str
    method_type: PaymentMethodType
    last_four: str | None = None
    brand: str | None = None
    is_default: bool
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

