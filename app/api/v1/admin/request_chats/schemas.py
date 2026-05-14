from pydantic import BaseModel, Field

from app.core.constants import PromptCategory


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
