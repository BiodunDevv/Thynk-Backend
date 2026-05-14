from pydantic import BaseModel, Field

from app.core.constants import (
    PromptCategory,
    PromptComplexity,
    PromptOutputFormat,
    PromptPlatform,
    PromptTone,
)


class GeneratePromptRequest(BaseModel):
    rough_input: str = Field(..., min_length=3, description="User's rough prompt idea.")
    title: str = Field(default="Untitled Prompt", max_length=120)
    category: PromptCategory
    tone: PromptTone
    platform: PromptPlatform
    complexity: PromptComplexity
    output_format: PromptOutputFormat
    auto_save: bool = True


class TestAIRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        description="Raw input sent to the configured AI provider for connectivity and output testing.",
        examples=["Write a polished product design prompt for a mobile onboarding flow."],
    )


class PromptResponse(BaseModel):
    id: str
    title: str
    rough_input: str
    generated_prompt: str
    category: PromptCategory
    tone: PromptTone
    platform: PromptPlatform
    complexity: PromptComplexity
    output_format: PromptOutputFormat
    is_favorite: bool
    collection_id: str | None = None


class PromptGenerationResult(BaseModel):
    prompt: PromptResponse
    remaining_generation_count: int
    upgrade_required: bool = False


class TestAIResponse(BaseModel):
    provider: str
    model: str
    deployment: str | None = None
    endpoint: str | None = None
    api_version: str | None = None
    output: str
    token_usage: int | None = None
