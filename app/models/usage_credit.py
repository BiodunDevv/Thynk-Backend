from datetime import datetime

from app.models.base import TimestampedDocument


class UsageCredit(TimestampedDocument):
    user_id: str
    source: str
    amount: int
    remaining: int
    expires_at: datetime | None = None
    created_by_admin_id: str | None = None

    class Settings:
        name = "usage_credits"
