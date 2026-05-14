from typing import Any

from pydantic import Field

from app.models.base import TimestampedDocument


class SupportActivity(TimestampedDocument):
    ticket_id: str
    actor_id: str | None = None
    actor_type: str
    action: str
    old_value: str | None = None
    new_value: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "support_activities"
        indexes = ["ticket_id", "created_at"]
