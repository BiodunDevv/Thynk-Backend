from app.api.v1.payments.service import reconcile_user_billing_state
from app.api.v1.subscriptions.schemas import SubscriptionResponse
from app.models.user import User
from app.services.notifications.notification_service import NotificationService

notification_service = NotificationService()


async def get_my_subscription(user: User) -> SubscriptionResponse | None:
    user, subscription, _ = await reconcile_user_billing_state(user)
    if not subscription:
        return None
    await notification_service.ensure_subscription_notifications(user)
    return SubscriptionResponse.model_validate(subscription.model_dump(mode="json"))
