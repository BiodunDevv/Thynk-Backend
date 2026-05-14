from app.core.constants import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.services.push.expo_client import ExpoClient


class PushService:
    def __init__(self) -> None:
        self.client = ExpoClient()

    async def notify_user(self, user: User, title: str, body: str, kind: NotificationType, data: dict | None = None) -> Notification:
        notification = Notification(user_id=user.id, title=title, body=body, type=kind, data=data or {})
        await notification.insert()
        await self.client.send(user.expo_push_tokens, title, body, data)
        return notification
