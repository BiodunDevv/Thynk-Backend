from app.api.v1.prompts.schemas import (
    EnhancePromptRequest,
    EnhancePromptResponse,
    GeneratePromptRequest,
    PromptGenerationResult,
    PromptResponse,
    PromptImageInput,
    TestAIResponse,
)
from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.prompt import Prompt
from app.models.user import User
from app.services.ai.base import get_ai_service
from app.services.ai.clarification_types import ClarificationResult
from app.services.ai.prompt_builder import (
    build_enhancement_instruction,
    build_generation_instruction_from_enhanced,
)
from app.services.ai.usage_tracker import UsageTracker

usage_tracker = UsageTracker()

_free_test_used: set[str] = set()


def serialize_images(images: list[PromptImageInput]) -> list[dict]:
    return [image.model_dump() for image in images]


async def enhance_prompt_input(payload: EnhancePromptRequest) -> EnhancePromptResponse:
    ai_service = get_ai_service()
    instruction = build_enhancement_instruction(
        rough_input=payload.rough_input,
        category=payload.category.value,
        tone=payload.tone.value,
        platform=payload.platform.value,
        complexity=payload.complexity.value,
        output_format=payload.output_format.value,
    )
    result = await ai_service.generate_prompt(
        instruction,
        images=serialize_images(payload.images),
        system_prompt=(
            "You are Thynk's prompt preprocessor. Transform raw user intent into a clean, concise, structured brief. "
            "Return only the improved brief."
        ),
    )
    settings = get_settings()
    return EnhancePromptResponse(
        provider=settings.ai_provider,
        model=result.get("model", "unknown"),
        enhanced_input=result.get("content", "").strip(),
        token_usage=result.get("token_usage"),
    )


async def generate_prompt(user: User, payload: GeneratePromptRequest) -> PromptGenerationResult:
    if not payload.rough_input.strip():
        raise AppException(400, "Prompt input is required.", ErrorCodes.PROMPT_INPUT_REQUIRED)
    usage = await usage_tracker.ensure_generation_allowed(user)
    ai_service = get_ai_service()
    enhanced_input = payload.rough_input.strip()
    if payload.enhance_input:
        enhanced = await enhance_prompt_input(
            EnhancePromptRequest(
                rough_input=payload.rough_input,
                category=payload.category,
                tone=payload.tone,
                platform=payload.platform,
                complexity=payload.complexity,
                output_format=payload.output_format,
                images=payload.images,
            )
        )
        enhanced_input = enhanced.enhanced_input
    instruction = build_generation_instruction_from_enhanced(
        enhanced_input=enhanced_input,
        category=payload.category.value,
        tone=payload.tone.value,
        platform=payload.platform.value,
        complexity=payload.complexity.value,
        output_format=payload.output_format.value,
    )
    result = await ai_service.generate_prompt(
        instruction,
        images=serialize_images(payload.images),
        system_prompt=(
            "You are Thynk's AI prompt generation engine. Produce a polished, high-quality prompt tailored to the user's selected platform and output format."
        ),
    )
    prompt = Prompt(
        user_id=user.id,
        title=payload.title,
        rough_input=payload.rough_input,
        enhanced_input=enhanced_input,
        generated_prompt=result["content"],
        image_urls=[image.image_url for image in payload.images],
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


async def free_test_generate(prompt: str, client_ip: str) -> dict:
    if client_ip in _free_test_used:
        raise AppException(429, "You have used your free test. Sign up for 5 free generations per week.", ErrorCodes.PROMPT_LIMIT_REACHED)
    _free_test_used.add(client_ip)
    ai_service = get_ai_service()
    clarification = ClarificationResult.model_validate(
        await ai_service.generate_clarification(
            {
                "chat_id": "free-test",
                "title": "Free test clarification",
                "category": "general",
                "source": "assistant_chat",
                "final_prompt_count": 0,
                "clarification_turn_count": 0,
                "has_images": False,
                "latest_user_message": prompt.strip(),
                "conversation": [
                    {
                        "role": "user",
                        "content": prompt.strip(),
                        "type": None,
                        "image_count": 0,
                        "clarification_complete": False,
                        "next_action": None,
                    }
                ],
            }
        )
    )
    if clarification.questions:
        content = "\n".join(
            f"{index + 1}. {question.question}"
            for index, question in enumerate(clarification.questions)
        )
    else:
        content = (
            clarification.reasoning_summary
            or "Thynk has enough context to help you generate a polished prompt."
        )
    return {"content": content, "used": True}


async def list_prompts(user: User) -> list[PromptResponse]:
    prompts = await Prompt.find(Prompt.user_id == user.id).sort("-created_at").to_list()
    return [PromptResponse.model_validate(prompt.model_dump()) for prompt in prompts]


async def test_ai_provider(raw_prompt: str, images: list[PromptImageInput] | None = None) -> TestAIResponse:
    if not raw_prompt.strip():
        raise AppException(400, "Prompt input is required.", ErrorCodes.PROMPT_INPUT_REQUIRED)
    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(
        raw_prompt.strip(),
        images=serialize_images(images or []),
        system_prompt=(
            "You are Thynk's AI provider test path. Respond normally to the user's request and use any provided images as context."
        ),
    )
    settings = get_settings()
    return TestAIResponse(
        provider=settings.ai_provider,
        model=result.get("model", "unknown"),
        deployment=settings.azure_openai_deployment_name,
        endpoint=settings.azure_openai_base_url,
        api_version=settings.azure_openai_api_version,
        image_count=len(images or []),
        output=result.get("content", ""),
        token_usage=result.get("token_usage"),
    )
