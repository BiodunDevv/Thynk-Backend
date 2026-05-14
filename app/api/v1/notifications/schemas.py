from pydantic import BaseModel

from app.core.constants import NotificationType


class PushTokenRequest(BaseModel):
    token: str


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    type: NotificationType
    data: dict
    is_read: bool
