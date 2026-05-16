from datetime import datetime

from pydantic import BaseModel, Field

from app.api.v1.subscriptions.schemas import SubscriptionResponse


class InitializePaymentRequest(BaseModel):
    plan_id: str
    provider: str = Field(default="paystack", examples=["paystack"])
    coupon_code: str | None = None
    callback_url: str | None = None


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    user_email: str | None = None
    plan_id: str
    plan_name: str | None = None
    provider: str
    provider_reference: str
    amount: float
    currency: str
    status: str
    metadata: dict
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaymentPlanSnapshotResponse(BaseModel):
    plan_id: str
    name: str | None = None
    slug: str | None = None
    billing_interval: str | None = None
    plan_currency: str | None = None
    plan_amount: float | None = None
    provider_currency: str | None = None
    provider_amount: float | None = None


class PaymentRecordResponse(PaymentResponse):
    plan_snapshot: PaymentPlanSnapshotResponse | None = None


class ProviderStatusResponse(BaseModel):
    provider: str
    reference: str | None = None
    status: str
    event: str | None = None
    message: str | None = None
    source: str


class BillingStateResponse(BaseModel):
    current_plan_id: str | None = None
    subscription_id: str | None = None
    subscription_status: str
    payment_status: str
    granted: bool
    resolved_via: str


class PaymentVerificationResponse(BaseModel):
    payment: PaymentRecordResponse
    plan_snapshot: PaymentPlanSnapshotResponse | None = None
    subscription: SubscriptionResponse | None = None
    billing_state: BillingStateResponse
    provider_status: ProviderStatusResponse
    provider_debug: dict | None = None
    already_verified: bool = False
