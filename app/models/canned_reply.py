from app.models.base import TimestampedDocument


class CannedReply(TimestampedDocument):
    title: str
    category: str
    body: str
    is_active: bool = True
    created_by: str | None = None

    class Settings:
        name = "canned_replies"
