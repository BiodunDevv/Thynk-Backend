from app.core.constants import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.services.push.expo_client import ExpoClient
from app.services.push.web_push_service import WebPushService


class PushService:
    def __init__(self) -> None:
        self.client = ExpoClient()
        self.web_push = WebPushService()

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
        if user.web_push_subscriptions:
            try:
                subscriptions = [
                    subscription.model_dump(mode="json")
                    if hasattr(subscription, "model_dump")
                    else subscription
                    for subscription in user.web_push_subscriptions
                ]
                await self.web_push.send(subscriptions, title, body, payload)
            except Exception:
                pass
        return notification
