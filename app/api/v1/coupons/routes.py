from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.coupons.schemas import CouponCreateRequest, CouponResponse, CouponValidateRequest
from app.api.v1.coupons.service import create_coupon, list_coupons, validate_coupon
from app.core.exceptions import AppException
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.coupon import Coupon
from app.models.user import User

router = APIRouter(prefix="/coupons", tags=["Coupons"])
admin_router = APIRouter(prefix="/admin/coupons", tags=["Admin Coupons"])


@router.post("/validate", response_model=SuccessResponse[dict], summary="Validate coupon")
async def validate(payload: CouponValidateRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Coupon validated successfully.", data=await validate_coupon(user, payload))


@admin_router.get("", response_model=SuccessResponse[list[CouponResponse]], summary="List coupons")
async def index(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Coupons fetched successfully.", data=await list_coupons())


@admin_router.get("/{coupon_id}", response_model=SuccessResponse[CouponResponse], summary="Get coupon by ID")
async def get_coupon(coupon_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    c = await Coupon.get(coupon_id)
    if not c:
        raise AppException(404, "Coupon not found.", "NOT_FOUND")
    return SuccessResponse(message="Coupon fetched successfully.", data=CouponResponse.model_validate(c.model_dump()))


@admin_router.post("", response_model=SuccessResponse[CouponResponse], status_code=status.HTTP_201_CREATED, summary="Create coupon")
async def create(payload: CouponCreateRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Coupon created successfully.", data=await create_coupon(admin.id, payload))


@admin_router.patch("/{coupon_id}/toggle", response_model=SuccessResponse[CouponResponse], summary="Toggle coupon active status")
async def toggle_coupon(coupon_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    c = await Coupon.get(coupon_id)
    if not c:
        raise AppException(404, "Coupon not found.", "NOT_FOUND")
    c.is_active = not c.is_active
    await c.save()
    return SuccessResponse(message=f"Coupon {'activated' if c.is_active else 'deactivated'}.", data=CouponResponse.model_validate(c.model_dump()))


@admin_router.delete("/{coupon_id}", response_model=SuccessResponse[dict], summary="Delete coupon")
async def delete_coupon(coupon_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    c = await Coupon.get(coupon_id)
    if not c:
        raise AppException(404, "Coupon not found.", "NOT_FOUND")
    await c.delete()
    return SuccessResponse(message="Coupon deleted successfully.", data={"id": coupon_id})
