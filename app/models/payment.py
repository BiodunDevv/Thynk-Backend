from typing import Any
from datetime import datetime

from pydantic import Field

from app.core.constants import PaymentStatus
from app.models.base import TimestampedDocument


class Payment(TimestampedDocument):
    user_id: str
    plan_id: str
    provider: str
    provider_reference: str = Field(unique=True)
    provider_customer_id: str | None = None
    amount: float
    currency: str
    status: PaymentStatus = PaymentStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)
    coupon_id: str | None = None
    discount_amount: float = 0

    class Settings:
        name = "payments"
        indexes = ["provider_reference", "user_id", "created_at"]


class PaymentWebhookEvent(TimestampedDocument):
    provider: str
    event_id: str
    provider_reference: str | None = None
    payment_id: str | None = None
    processing_status: str = "accepted"
    processing_message: str | None = None
    transition_source: str | None = None
    processed_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "payment_webhook_events"
        indexes = ["provider", "event_id", "provider_reference", "payment_id"]
