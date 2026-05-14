from datetime import datetime, timezone
from uuid import uuid4

from beanie import Document
from pydantic import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampedDocument(Document):
    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    async def save(self, *args, **kwargs):
        self.updated_at = utc_now()
        return await super().save(*args, **kwargs)
