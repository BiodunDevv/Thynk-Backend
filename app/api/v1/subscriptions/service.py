from app.api.v1.subscriptions.schemas import SubscriptionResponse
from app.models.subscription import Subscription
from app.models.user import User


async def get_my_subscription(user: User) -> SubscriptionResponse | None:
    if not user.subscription_id:
        return None
    subscription = await Subscription.get(user.subscription_id)
    return SubscriptionResponse.model_validate(subscription.model_dump()) if subscription else None
