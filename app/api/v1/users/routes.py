from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.common import UserResponse
from app.api.v1.users.schemas import UpdateProfileRequest
from app.api.v1.users.service import get_profile, soft_delete_user, update_profile
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users", "Profile"])


@router.get("/me", response_model=SuccessResponse[UserResponse], response_model_exclude_none=True, summary="Get current user profile", description="Returns the logged-in user's profile.")
async def read_profile(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Profile fetched successfully.", data=await get_profile(user))


@router.get("/profile", response_model=SuccessResponse[UserResponse], response_model_exclude_none=True, summary="Get current user profile", description="Returns the logged-in user's profile using a cleaner frontend-friendly path.")
async def read_profile_alias(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Profile fetched successfully.", data=await get_profile(user))


@router.patch("/me", response_model=SuccessResponse[UserResponse], response_model_exclude_none=True, summary="Update profile", description="Updates the logged-in user's profile.")
async def patch_profile(payload: UpdateProfileRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Profile updated successfully.", data=await update_profile(user, payload))


@router.delete("/me", response_model=SuccessResponse[dict], summary="Delete account", description="Soft deletes the logged-in user's account.")
async def delete_account(user: User = Depends(get_current_user)):
    await soft_delete_user(user)
    return SuccessResponse(message="Account deleted successfully.", data={})
