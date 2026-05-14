from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import RequestChatSource, RequestChatStatus
from app.models.base import TimestampedDocument


class RequestChatMessage(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    token_usage: int | None = None
    model_used: str | None = None
    created_at: datetime


class RequestChat(TimestampedDocument):
    user_id: str
    title: str
    category: str
    status: RequestChatStatus = RequestChatStatus.ACTIVE
    source: RequestChatSource = RequestChatSource.PROMPT_GENERATOR
    messages: list[RequestChatMessage] = Field(default_factory=list)
    generated_prompt_ids: list[str] = Field(default_factory=list)
    is_favorite: bool = False
    is_reported: bool = False
    reported_reason: str | None = None
    deleted_at: datetime | None = None
    admin_notes: list[str] = Field(default_factory=list)

    class Settings:
        name = "request_chats"
        indexes = ["user_id", "category", "status", "is_reported", "created_at"]
