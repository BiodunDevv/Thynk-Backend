from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.notifications.schemas import NotificationResponse, PushTokenRequest
from app.api.v1.notifications.service import list_notifications, register_push_token, remove_push_token
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/register-token", response_model=SuccessResponse[dict], summary="Register device push token", description="Registers a device push token for the current user.")
async def register_token(payload: PushTokenRequest, user: User = Depends(get_current_user)):
    await register_push_token(user, payload.token)
    return SuccessResponse(message="Push token registered successfully.", data={})


@router.delete("/remove-token", response_model=SuccessResponse[dict], summary="Remove device push token", description="Removes a device push token from the current user.")
async def unregister_token(payload: PushTokenRequest, user: User = Depends(get_current_user)):
    await remove_push_token(user, payload.token)
    return SuccessResponse(message="Push token removed successfully.", data={})


@router.get("", response_model=SuccessResponse[list[NotificationResponse]], summary="List notifications", description="Returns the current user's notification history.")
async def my_notifications(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Notifications fetched successfully.", data=await list_notifications(user))
