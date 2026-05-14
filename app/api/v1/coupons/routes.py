from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.coupons.schemas import CouponCreateRequest, CouponResponse, CouponValidateRequest
from app.api.v1.coupons.service import create_coupon, list_coupons, validate_coupon
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/coupons", tags=["Coupons"])
admin_router = APIRouter(prefix="/admin/coupons", tags=["Admin Coupons"])


@router.post("/validate", response_model=SuccessResponse[dict], summary="Validate coupon", description="Validates a coupon before payment initialization.")
async def validate(payload: CouponValidateRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Coupon validated successfully.", data=await validate_coupon(user, payload))


@admin_router.post("", response_model=SuccessResponse[CouponResponse], status_code=status.HTTP_201_CREATED, summary="Create coupon", description="Creates a coupon. Requires Bearer token with SUPER_ADMIN role.")
async def create(payload: CouponCreateRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Coupon created successfully.", data=await create_coupon(admin.id, payload))


@admin_router.get("", response_model=SuccessResponse[list[CouponResponse]], summary="List coupons", description="Returns all coupons. Requires Bearer token with SUPER_ADMIN role.")
async def index(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Coupons fetched successfully.", data=await list_coupons())
