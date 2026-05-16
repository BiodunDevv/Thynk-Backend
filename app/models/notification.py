from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.constants import NotificationType
from app.models.base import TimestampedDocument


class Notification(TimestampedDocument):
    user_id: str
    title: str
    body: str
    type: NotificationType
    data: dict[str, Any] = Field(default_factory=dict)
    dedupe_key: str | None = None
    is_read: bool = False
    read_at: datetime | None = None

    class Settings:
        name = "notifications"
