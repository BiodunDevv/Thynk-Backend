from app.api.v1.prompts.schemas import (
    GeneratePromptRequest,
    PromptGenerationResult,
    PromptResponse,
    TestAIResponse,
)
from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.prompt import Prompt
from app.models.user import User
from app.services.ai.base import get_ai_service
from app.services.ai.prompt_builder import build_prompt_instruction
from app.services.ai.usage_tracker import UsageTracker

usage_tracker = UsageTracker()


async def generate_prompt(user: User, payload: GeneratePromptRequest) -> PromptGenerationResult:
    if not payload.rough_input.strip():
        raise AppException(400, "Prompt input is required.", ErrorCodes.PROMPT_INPUT_REQUIRED)
    usage = await usage_tracker.ensure_generation_allowed(user)
    instruction = build_prompt_instruction(payload)
    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(instruction)
    prompt = Prompt(
        user_id=user.id,
        title=payload.title,
        rough_input=payload.rough_input,
        generated_prompt=result["content"],
        category=payload.category,
        tone=payload.tone,
        platform=payload.platform,
        complexity=payload.complexity,
        output_format=payload.output_format,
    )
    if payload.auto_save:
        await prompt.insert()
    return PromptGenerationResult(
        prompt=PromptResponse.model_validate(prompt.model_dump()),
        remaining_generation_count=usage["remaining_generations"],
        upgrade_required=False,
    )


async def list_prompts(user: User) -> list[PromptResponse]:
    prompts = await Prompt.find(Prompt.user_id == user.id).sort("-created_at").to_list()
    return [PromptResponse.model_validate(prompt.model_dump()) for prompt in prompts]


async def test_ai_provider(raw_prompt: str) -> TestAIResponse:
    if not raw_prompt.strip():
        raise AppException(400, "Prompt input is required.", ErrorCodes.PROMPT_INPUT_REQUIRED)
    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(raw_prompt.strip())
    settings = get_settings()
    return TestAIResponse(
        provider=settings.ai_provider,
        model=result.get("model", "unknown"),
        deployment=settings.azure_openai_deployment_name,
        endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        output=result.get("content", ""),
        token_usage=result.get("token_usage"),
    )
