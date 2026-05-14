from app.core.constants import PromptCategory
from pydantic import Field

from app.models.base import TimestampedDocument


class PromptTemplate(TimestampedDocument):
    title: str
    description: str
    category: PromptCategory
    template_content: str
    tags: list[str] = Field(default_factory=list)
    is_premium: bool = False
    is_active: bool = True

    class Settings:
        name = "prompt_templates"
