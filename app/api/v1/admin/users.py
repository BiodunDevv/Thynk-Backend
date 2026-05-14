from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.common import UserResponse
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.usage_credit import UsageCredit
from app.models.user import User

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


class GrantCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0)
    reason: str


@router.get("", response_model=SuccessResponse[list[UserResponse]], summary="List users", description="Returns users for admin management. Requires Bearer token with SUPER_ADMIN role.")
async def list_users(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    users = await User.find_all().sort("-created_at").to_list()
    return SuccessResponse(message="Users fetched successfully.", data=[UserResponse.model_validate(user.model_dump()) for user in users])


@router.post("/{user_id}/grant-credits", response_model=SuccessResponse[dict], summary="Grant AI usage credits", description="Grants extra AI credits to a user. Requires Bearer token with SUPER_ADMIN role.")
async def grant_credits(user_id: str, payload: GrantCreditsRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    credit = UsageCredit(user_id=user_id, source="admin_grant", amount=payload.amount, remaining=payload.amount, created_by_admin_id=admin.id)
    await credit.insert()
    return SuccessResponse(message="AI credits granted successfully.", data={"user_id": user_id, "credits_added": credit.amount, "remaining_credits": credit.remaining})
