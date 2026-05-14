from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import RequestChatSource, RequestChatStatus


class RequestChatMessagePayload(BaseModel):
    content: str = Field(..., min_length=1)


class RequestChatCreateRequest(BaseModel):
    title: str
    category: str
    source: RequestChatSource = RequestChatSource.ASSISTANT_CHAT
    message: str = Field(..., min_length=1)


class RequestChatUpdateRequest(BaseModel):
    title: str | None = None
    status: RequestChatStatus | None = None


class ReportChatRequest(BaseModel):
    reason: str = Field(..., min_length=3)


class RequestChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict
    token_usage: int | None = None
    model_used: str | None = None
    created_at: datetime


class RequestChatResponse(BaseModel):
    id: str
    title: str
    category: str
    status: RequestChatStatus
    source: RequestChatSource
    messages: list[RequestChatMessageResponse]
    generated_prompt_ids: list[str]
    is_favorite: bool
    is_reported: bool
    reported_reason: str | None = None
