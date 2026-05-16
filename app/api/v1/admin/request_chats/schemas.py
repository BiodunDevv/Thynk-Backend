from pydantic import BaseModel, Field

from app.core.constants import PromptCategory
from app.core.constants import RequestChatStatus


class AdminRequestChatOutputResponse(BaseModel):
    id: str
    content: str
    created_at: str | None = None
    model_used: str | None = None
    token_usage: int | None = None


class AdminRequestChatResponse(BaseModel):
    id: str
    user_id: str
    title: str
    category: str
    status: RequestChatStatus
    is_reported: bool
    created_at: str | None = None
    updated_at: str | None = None
    generated_prompt_count: int = 0
    message_count: int = 0
    latest_output_preview: str | None = None
    final_outputs: list[AdminRequestChatOutputResponse] = Field(default_factory=list)


class ChatReviewRequest(BaseModel):
    reviewed: bool = True


class ChatArchiveRequest(BaseModel):
    status: str = "archived"


class AdminNoteRequest(BaseModel):
    note: str


class ConvertToTemplateRequest(BaseModel):
    title: str
    description: str
    category: PromptCategory
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
    is_active: bool = False
    template_content: str
    admin_notes: str | None = None
