from app.api.v1.notifications.schemas import NotificationResponse
from app.models.notification import Notification
from app.models.user import User


async def register_push_token(user: User, token: str) -> None:
    if token not in user.expo_push_tokens:
        user.expo_push_tokens.append(token)
        await user.save()


async def remove_push_token(user: User, token: str) -> None:
    user.expo_push_tokens = [item for item in user.expo_push_tokens if item != token]
    await user.save()


async def list_notifications(user: User) -> list[NotificationResponse]:
    records = await Notification.find(Notification.user_id == user.id).sort("-created_at").to_list()
    return [NotificationResponse.model_validate(item.model_dump()) for item in records]
