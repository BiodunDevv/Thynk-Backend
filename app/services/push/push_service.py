from app.core.constants import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.services.push.expo_client import ExpoClient


class PushService:
    def __init__(self) -> None:
        self.client = ExpoClient()

    async def notify_user(self, user: User, title: str, body: str, kind: NotificationType, data: dict | None = None) -> Notification:
        payload = data or {}
        notification = Notification(
            user_id=user.id,
            title=title,
            body=body,
            type=kind,
            data=payload,
            dedupe_key=payload.get("dedupe_key"),
        )
        await notification.insert()
        native_tokens = [
            token
            for token in user.expo_push_tokens
            if token and not token.startswith("web:")
        ]
        if native_tokens:
            try:
                await self.client.send(native_tokens, title, body, data)
            except Exception:
                # Notification history should still be preserved even if push delivery fails.
                pass
        return notification
