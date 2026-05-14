from app.core.constants import (
    PromptCategory,
    PromptComplexity,
    PromptOutputFormat,
    PromptPlatform,
    PromptTone,
)
from app.models.base import TimestampedDocument


class Prompt(TimestampedDocument):
    user_id: str
    title: str
    rough_input: str
    generated_prompt: str
    category: PromptCategory
    tone: PromptTone
    platform: PromptPlatform
    complexity: PromptComplexity
    output_format: PromptOutputFormat
    is_favorite: bool = False
    collection_id: str | None = None

    class Settings:
        name = "prompts"
        indexes = ["user_id", "category", "created_at"]
