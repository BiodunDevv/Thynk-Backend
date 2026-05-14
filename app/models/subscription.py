from datetime import datetime

from app.core.constants import SubscriptionStatus
from app.models.base import TimestampedDocument


class Subscription(TimestampedDocument):
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    provider: str
    provider_subscription_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False

    class Settings:
        name = "subscriptions"
