from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import CouponDiscountType


class CouponCreateRequest(BaseModel):
    code: str
    description: str | None = None
    discount_type: CouponDiscountType
    discount_value: float
    currency: str | None = None
    max_redemptions: int | None = None
    per_user_limit: int = 1
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    applicable_plan_ids: list[str] = Field(default_factory=list)
    minimum_amount: float = 0
    is_active: bool = True


class CouponUpdateRequest(BaseModel):
    description: str | None = None
    discount_type: CouponDiscountType | None = None
    discount_value: float | None = None
    currency: str | None = None
    max_redemptions: int | None = None
    per_user_limit: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    applicable_plan_ids: list[str] | None = None
    minimum_amount: float | None = None
    is_active: bool | None = None


class CouponValidateRequest(BaseModel):
    code: str
    plan_id: str
    amount: float


class CouponResponse(CouponCreateRequest):
    id: str
    redeemed_count: int
