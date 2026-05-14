from datetime import datetime

from app.core.constants import CouponDiscountType
from pydantic import Field

from app.models.base import TimestampedDocument


class Coupon(TimestampedDocument):
    code: str
    description: str | None = None
    discount_type: CouponDiscountType
    discount_value: float
    currency: str | None = None
    max_redemptions: int | None = None
    redeemed_count: int = 0
    per_user_limit: int = 1
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    applicable_plan_ids: list[str] = Field(default_factory=list)
    minimum_amount: float = 0
    is_active: bool = True
    created_by: str | None = None

    class Settings:
        name = "coupons"
        indexes = ["code", "created_at"]


class CouponRedemption(TimestampedDocument):
    coupon_id: str
    user_id: str
    payment_id: str | None = None

    class Settings:
        name = "coupon_redemptions"
