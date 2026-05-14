from pydantic import BaseModel, Field

from app.core.constants import PromptCategory


class TemplateCreateRequest(BaseModel):
    title: str
    description: str
    category: PromptCategory
    template_content: str
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
    is_active: bool = True


class TemplateResponse(TemplateCreateRequest):
    id: str
