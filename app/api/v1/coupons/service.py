from app.api.v1.coupons.schemas import CouponCreateRequest, CouponResponse, CouponValidateRequest
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.coupon import Coupon, CouponRedemption
from app.models.user import User
from app.utils.datetime import ensure_utc, utc_now


async def create_coupon(admin_id: str, payload: CouponCreateRequest) -> CouponResponse:
    coupon = Coupon(**payload.model_dump(), code=payload.code.upper(), created_by=admin_id)
    await coupon.insert()
    return CouponResponse.model_validate(coupon.model_dump())


async def list_coupons() -> list[CouponResponse]:
    coupons = await Coupon.find_all().sort("-created_at").to_list()
    return [CouponResponse.model_validate(item.model_dump()) for item in coupons]


async def validate_coupon(user: User, payload: CouponValidateRequest) -> dict:
    coupon = await Coupon.find_one(Coupon.code == payload.code.upper())
    if not coupon:
        raise AppException(404, "Coupon not found.", ErrorCodes.COUPON_NOT_FOUND)
    if not coupon.is_active:
        raise AppException(400, "Coupon is inactive.", ErrorCodes.COUPON_INACTIVE)
    now = utc_now()
    valid_from = ensure_utc(coupon.valid_from) if coupon.valid_from else None
    valid_until = ensure_utc(coupon.valid_until) if coupon.valid_until else None
    if (valid_from and valid_from > now) or (valid_until and valid_until < now):
        raise AppException(400, "Coupon has expired.", ErrorCodes.COUPON_EXPIRED)
    if coupon.max_redemptions is not None and coupon.redeemed_count >= coupon.max_redemptions:
        raise AppException(400, "Coupon usage limit reached.", ErrorCodes.COUPON_USAGE_LIMIT_REACHED)
    user_redemptions = await CouponRedemption.find(CouponRedemption.coupon_id == coupon.id, CouponRedemption.user_id == user.id).count()
    if user_redemptions >= coupon.per_user_limit:
        raise AppException(400, "Coupon user limit reached.", ErrorCodes.COUPON_USER_LIMIT_REACHED)
    if coupon.applicable_plan_ids and payload.plan_id not in coupon.applicable_plan_ids:
        raise AppException(400, "Coupon is not applicable to this plan.", ErrorCodes.COUPON_PLAN_NOT_APPLICABLE)
    discount = payload.amount * (coupon.discount_value / 100) if coupon.discount_type.value == "percentage" else coupon.discount_value
    return {"coupon": CouponResponse.model_validate(coupon.model_dump()), "discount_amount": discount, "final_amount": max(payload.amount - discount, 0)}
