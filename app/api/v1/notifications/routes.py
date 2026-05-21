from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.notifications.schemas import (
    NotificationResponse,
    NotificationSummaryResponse,
    PushTokenRequest,
    WebPushSubscriptionRemoveRequest,
    WebPushSubscriptionRequest,
)
from app.api.v1.notifications.service import (
    delete_notification,
    get_notification_summary,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    register_web_push_subscription,
    register_push_token,
    remove_web_push_subscription,
    remove_push_token,
    send_test_notification,
)
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


@router.post(
    "/web-push",
    response_model=SuccessResponse[dict],
    summary="Register browser push subscription",
    description="Registers or updates a real browser Push API subscription for the current user. This is used for background web push on supported browsers.",
)
async def register_web_push(payload: WebPushSubscriptionRequest, user: User = Depends(get_current_user)):
    await register_web_push_subscription(user, payload)
    return SuccessResponse(message="Browser push subscription registered successfully.", data={})


@router.delete(
    "/web-push",
    response_model=SuccessResponse[dict],
    summary="Remove browser push subscription",
    description="Removes a browser Push API subscription for the current user on this device/browser.",
)
async def unregister_web_push(payload: WebPushSubscriptionRemoveRequest, user: User = Depends(get_current_user)):
    await remove_web_push_subscription(user, payload.endpoint)
    return SuccessResponse(message="Browser push subscription removed successfully.", data={})


@router.get("/summary", response_model=SuccessResponse[NotificationSummaryResponse], summary="Get notification summary", description="Returns unread notification count and registered browser/device status.")
async def notification_summary(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Notification summary fetched successfully.", data=await get_notification_summary(user))


@router.get("", response_model=SuccessResponse[list[NotificationResponse]], summary="List notifications", description="Returns the current user's notification history.")
async def my_notifications(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Notifications fetched successfully.", data=await list_notifications(user))


@router.patch("/read-all", response_model=SuccessResponse[dict], summary="Mark all notifications as read", description="Marks every notification for the current user as read.")
async def read_all_notifications(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Notifications marked as read.", data=await mark_all_notifications_read(user))


@router.patch("/{notification_id}/read", response_model=SuccessResponse[NotificationResponse], summary="Mark notification as read", description="Marks a specific notification as read.")
async def read_notification(notification_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Notification marked as read.", data=await mark_notification_read(user, notification_id))


@router.delete(
    "/{notification_id}",
    response_model=SuccessResponse[dict],
    summary="Delete notification",
    description="Deletes a specific notification for the current user.",
)
async def remove_notification(notification_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Notification deleted successfully.", data=await delete_notification(user, notification_id))


@router.post("/test", response_model=SuccessResponse[NotificationResponse], summary="Send a test notification", description="Creates a test notification and attempts push delivery for the current user.")
async def test_notification(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Test notification sent successfully.", data=await send_test_notification(user))
