from typing import Any

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
    payload: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "payment_webhook_events"
        indexes = ["provider", "event_id"]
