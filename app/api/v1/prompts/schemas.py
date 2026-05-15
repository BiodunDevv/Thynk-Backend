from pydantic import BaseModel, Field, field_validator

from app.core.constants import (
    PromptCategory,
    PromptComplexity,
    PromptOutputFormat,
    PromptPlatform,
    PromptTone,
)


class PromptImageInput(BaseModel):
    image_url: str = Field(
        ...,
        description="Public HTTPS image URL or base64 data URL provided to the AI model for visual context.",
        examples=["https://example.com/reference-ui.png"],
    )
    detail: str = Field(default="auto", description="Vision detail mode.", examples=["auto"])

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        if value.startswith("https://") or value.startswith("data:image/"):
            return value
        raise ValueError("Image input must be an HTTPS URL or a base64 data URL.")


class GeneratePromptRequest(BaseModel):
    rough_input: str = Field(..., min_length=3, description="User's rough prompt idea.")
    title: str = Field(default="Untitled Prompt", max_length=120)
    category: PromptCategory
    tone: PromptTone
    platform: PromptPlatform
    complexity: PromptComplexity
    output_format: PromptOutputFormat
    images: list[PromptImageInput] = Field(default_factory=list, max_length=4)
    enhance_input: bool = True
    auto_save: bool = True


class TestAIRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        description="Raw input sent to the configured AI provider for connectivity and output testing.",
        examples=["Write a polished product design prompt for a mobile onboarding flow."],
    )
    images: list[PromptImageInput] = Field(default_factory=list, max_length=4)


class EnhancePromptRequest(BaseModel):
    rough_input: str = Field(
        ...,
        min_length=3,
        description="Raw user idea that should be clarified before final prompt generation.",
    )
    category: PromptCategory
    tone: PromptTone
    platform: PromptPlatform
    complexity: PromptComplexity
    output_format: PromptOutputFormat
    images: list[PromptImageInput] = Field(default_factory=list, max_length=4)


class EnhancePromptResponse(BaseModel):
    provider: str
    model: str
    enhanced_input: str
    token_usage: int | None = None


class PromptResponse(BaseModel):
    id: str
    title: str
    rough_input: str
    enhanced_input: str | None = None
    generated_prompt: str
    image_urls: list[str] = Field(default_factory=list)
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
    image_count: int = 0
    output: str
    token_usage: int | None = None


class FreeTestRequest(BaseModel):
    prompt: str = Field(..., min_length=3)


class FreeTestResponse(BaseModel):
    content: str
    used: bool
