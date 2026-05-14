from pydantic import BaseModel, Field


class InitializePaymentRequest(BaseModel):
    plan_id: str
    provider: str = Field(default="paystack", examples=["paystack"])
    coupon_code: str | None = None
    callback_url: str | None = None


class PaymentResponse(BaseModel):
    id: str
    provider: str
    provider_reference: str
    amount: float
    currency: str
    status: str
    metadata: dict
