from pydantic import BaseModel

from app.core.constants import NotificationType


class PushTokenRequest(BaseModel):
    token: str


class NotificationSummaryResponse(BaseModel):
    unread_count: int
    registered_devices: int
    has_browser_token: bool


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    type: NotificationType
    data: dict
    is_read: bool
    read_at: str | None = None
    created_at: str
