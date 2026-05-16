from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.common import UserResponse
from app.core.exceptions import AppException
from app.core.error_codes import ErrorCodes
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.prompt import Prompt
from app.models.request_chat import RequestChat
from app.models.usage_credit import UsageCredit
from app.models.user import User

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


class GrantCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0)
    reason: str


@router.get("", response_model=SuccessResponse[list[UserResponse]], summary="List users")
async def list_users(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    users = await User.find_all().sort("-created_at").to_list()
    return SuccessResponse(message="Users fetched successfully.", data=[UserResponse.model_validate(user.model_dump()) for user in users])


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse], summary="Get user by ID")
async def get_user(user_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    return SuccessResponse(message="User fetched successfully.", data=UserResponse.model_validate(user.model_dump()))


@router.patch("/{user_id}/toggle-status", response_model=SuccessResponse[UserResponse], summary="Toggle user active status")
async def toggle_user_status(user_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    user.is_active = not user.is_active
    await user.save()
    return SuccessResponse(message=f"User {'activated' if user.is_active else 'deactivated'} successfully.", data=UserResponse.model_validate(user.model_dump()))


@router.post("/{user_id}/grant-credits", response_model=SuccessResponse[dict], summary="Grant AI usage credits")
async def grant_credits(user_id: str, payload: GrantCreditsRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    credit = UsageCredit(user_id=user_id, source="admin_grant", amount=payload.amount, remaining=payload.amount, created_by_admin_id=admin.id)
    await credit.insert()
    return SuccessResponse(message="AI credits granted successfully.", data={"user_id": user_id, "credits_added": credit.amount, "remaining_credits": credit.remaining})


class GrantPromptsRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Number of extra prompt generations to grant")
    reason: str = Field(default="Admin grant")


@router.post("/{user_id}/grant-prompts", response_model=SuccessResponse[dict], summary="Grant extra prompt generations directly")
async def grant_prompts(user_id: str, payload: GrantPromptsRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    credit = UsageCredit(user_id=user_id, source="admin_grant", amount=payload.amount, remaining=payload.amount, created_by_admin_id=admin.id)
    await credit.insert()
    return SuccessResponse(
        message=f"{payload.amount} prompt generations granted.",
        data={"user_id": user_id, "prompts_granted": payload.amount, "monthly_count": user.monthly_generation_count},
    )


@router.get("/{user_id}/chats", response_model=SuccessResponse[list[dict]], summary="Get user's request chats")
async def get_user_chats(user_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    chats = await RequestChat.find(RequestChat.user_id == user_id).sort("-created_at").to_list()
    return SuccessResponse(
        message="User chats fetched.",
        data=[c.model_dump() for c in chats],
    )


# ── Admin prompts router ────────────────────────────────────────────────────
prompts_router = APIRouter(prefix="/admin/prompts", tags=["Admin Prompts"])


@prompts_router.get("", response_model=SuccessResponse[list[dict]], summary="List all generated prompts")
async def list_all_prompts(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    prompts = await Prompt.find_all().sort("-created_at").to_list()
    return SuccessResponse(
        message="Prompts fetched successfully.",
        data=[p.model_dump() for p in prompts],
    )
