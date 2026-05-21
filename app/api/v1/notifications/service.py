from app.api.v1.notifications.schemas import WebPushSubscriptionRequest
from app.api.v1.notifications.schemas import NotificationResponse
from app.models.user import WebPushSubscriptionKeys
from app.models.user import WebPushSubscription
from app.models.user import User
from app.utils.datetime import utc_now
from app.services.notifications.notification_service import NotificationService

notification_service = NotificationService()


async def register_push_token(user: User, token: str) -> None:
    normalized = notification_service.normalize_token(token)
    if normalized and normalized not in user.expo_push_tokens:
        user.expo_push_tokens.append(normalized)
        await user.save()


async def remove_push_token(user: User, token: str) -> None:
    normalized = notification_service.normalize_token(token)
    user.expo_push_tokens = [item for item in user.expo_push_tokens if item != normalized]
    await user.save()


async def register_web_push_subscription(user: User, payload: WebPushSubscriptionRequest) -> None:
    now = utc_now()
    existing = next(
        (item for item in user.web_push_subscriptions if item.endpoint == payload.endpoint),
        None,
    )
    if existing:
        existing.expirationTime = payload.expirationTime
        existing.keys.p256dh = payload.keys.p256dh
        existing.keys.auth = payload.keys.auth
        existing.origin = payload.origin
        existing.user_agent = payload.user_agent
        existing.updated_at = now
    else:
        user.web_push_subscriptions.append(
            WebPushSubscription(
                endpoint=payload.endpoint,
                expirationTime=payload.expirationTime,
                keys=WebPushSubscriptionKeys(
                    p256dh=payload.keys.p256dh,
                    auth=payload.keys.auth,
                ),
                origin=payload.origin,
                user_agent=payload.user_agent,
                created_at=now,
                updated_at=now,
            )
        )
    await user.save()


async def remove_web_push_subscription(user: User, endpoint: str) -> None:
    user.web_push_subscriptions = [
        item for item in user.web_push_subscriptions if item.endpoint != endpoint
    ]
    await user.save()


async def list_notifications(user: User) -> list[NotificationResponse]:
    await notification_service.ensure_subscription_notifications(user)
    await notification_service.ensure_usage_notifications(user)
    records = await notification_service.list_notifications(user)
    return [NotificationResponse.model_validate(item.model_dump(mode="json")) for item in records]


async def mark_notification_read(user: User, notification_id: str) -> NotificationResponse:
    notification = await notification_service.mark_read(user, notification_id)
    return NotificationResponse.model_validate(notification.model_dump(mode="json"))


async def mark_all_notifications_read(user: User) -> dict:
    count = await notification_service.mark_all_read(user)
    return {"marked_count": count}


async def delete_notification(user: User, notification_id: str) -> dict:
    await notification_service.delete_notification(user, notification_id)
    return {"deleted": True, "notification_id": notification_id}


async def send_test_notification(user: User) -> NotificationResponse:
    notification = await notification_service.send_test_notification(user)
    return NotificationResponse.model_validate(notification.model_dump(mode="json"))


async def get_notification_summary(user: User) -> dict:
    await notification_service.ensure_subscription_notifications(user)
    await notification_service.ensure_usage_notifications(user)
    return await notification_service.get_summary(user)
