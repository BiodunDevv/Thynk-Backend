from pydantic import Field

from app.models.base import TimestampedDocument


class SupportMessage(TimestampedDocument):
    ticket_id: str
    sender_id: str | None = None
    sender_type: str
    message: str
    attachments: list[dict] = Field(default_factory=list)
    is_internal_note: bool = False

    class Settings:
        name = "support_messages"
        indexes = ["ticket_id", "created_at"]
