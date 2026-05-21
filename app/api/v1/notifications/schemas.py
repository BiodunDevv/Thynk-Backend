from pydantic import BaseModel, Field

from app.core.constants import NotificationType


class PushTokenRequest(BaseModel):
    token: str


class WebPushSubscriptionKeysRequest(BaseModel):
    p256dh: str = Field(..., min_length=16)
    auth: str = Field(..., min_length=8)


class WebPushSubscriptionRequest(BaseModel):
    endpoint: str = Field(..., min_length=20)
    expirationTime: int | None = None
    keys: WebPushSubscriptionKeysRequest
    origin: str | None = None
    user_agent: str | None = None


class WebPushSubscriptionRemoveRequest(BaseModel):
    endpoint: str = Field(..., min_length=20)


class NotificationSummaryResponse(BaseModel):
    unread_count: int
    registered_devices: int
    has_browser_token: bool
    has_web_push_subscription: bool = False


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    type: NotificationType
    data: dict
    is_read: bool
    read_at: str | None = None
    created_at: str
