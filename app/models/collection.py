from app.models.base import TimestampedDocument


class Collection(TimestampedDocument):
    user_id: str
    name: str
    description: str | None = None

    class Settings:
        name = "collections"
