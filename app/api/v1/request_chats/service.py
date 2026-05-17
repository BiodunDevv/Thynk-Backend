import re
from uuid import uuid4

from app.api.v1.request_chats.schemas import (
    ReportChatRequest,
    RequestChatCreateRequest,
    RequestChatMessagePayload,
    RequestChatResponse,
    RequestChatUpdateRequest,
)
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.request_chat import RequestChat, RequestChatMessage
from app.models.user import User
from app.services.ai.clarification_service import (
    build_chat_state,
    build_clarification_metadata,
    build_generation_context,
    collect_all_image_urls,
    fallback_clarification,
)
from app.services.ai.clarification_types import ClarificationResult
from app.services.ai.usage_tracker import UsageTracker
from app.utils.datetime import utc_now

usage_tracker = UsageTracker()

PROMPT_SECTION_PATTERN = re.compile(r"## Prompt\s*([\s\S]*?)(?=\n## |\s*$)", re.IGNORECASE)
WHY_SECTION_PATTERN = re.compile(r"## Why this works\s*([\s\S]*?)(?=\n## |\s*$)", re.IGNORECASE)
BEST_USED_SECTION_PATTERN = re.compile(r"## Best used with\s*([\s\S]*?)(?=\n## |\s*$)", re.IGNORECASE)
PROMPT_STEP_CHAR_LIMIT = 2600
PROMPT_STEP_PARAGRAPH_LIMIT = 6


def serialize_chat(chat: RequestChat) -> RequestChatResponse:
    return RequestChatResponse.model_validate(chat.model_dump())


async def generate_clarification_for_chat(chat: RequestChat) -> ClarificationResult:
    from app.services.ai.base import get_ai_service

    ai_service = get_ai_service()
    try:
        chat_state = build_chat_state(chat)
        image_urls = collect_all_image_urls(chat)
        images = [{"image_url": url, "detail": "auto"} for url in image_urls]
        result = await ai_service.generate_clarification(chat_state, images=images if images else None)
        return ClarificationResult.model_validate(result)
    except AppException:
        raise
    except Exception:
        return fallback_clarification(chat)


def create_assistant_clarification_message(result: ClarificationResult) -> RequestChatMessage:
    if result.questions:
        content = "\n".join(f"- {item.question}" for item in result.questions)
    else:
        content = "I have enough context to generate the final prompt when you're ready."

    return RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=content,
        metadata=build_clarification_metadata(result),
        token_usage=0,
        model_used=None,
        created_at=utc_now(),
    )


def parse_prompt_document_sections(content: str) -> dict[str, str]:
    normalized = content.replace("\r\n", "\n").strip()
    prompt_match = PROMPT_SECTION_PATTERN.search(normalized)
    why_match = WHY_SECTION_PATTERN.search(normalized)
    best_used_match = BEST_USED_SECTION_PATTERN.search(normalized)
    return {
        "prompt": (prompt_match.group(1).strip() if prompt_match else normalized),
        "why": why_match.group(1).strip() if why_match else "",
        "best_used_with": best_used_match.group(1).strip() if best_used_match else "",
        "raw": normalized,
    }


def split_prompt_into_steps(prompt_text: str) -> list[dict[str, str]]:
    paragraphs = [paragraph.strip() for paragraph in prompt_text.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return [{"step": 1, "title": "Prompt step 1", "content": prompt_text.strip()}]

    steps: list[list[str]] = []
    current_step: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        would_exceed_length = current_length + paragraph_length > PROMPT_STEP_CHAR_LIMIT
        would_exceed_paragraphs = len(current_step) >= PROMPT_STEP_PARAGRAPH_LIMIT
        if current_step and (would_exceed_length or would_exceed_paragraphs):
            steps.append(current_step)
            current_step = []
            current_length = 0
        current_step.append(paragraph)
        current_length += paragraph_length

    if current_step:
        steps.append(current_step)

    if len(steps) <= 1:
        return [{"step": 1, "title": "Prompt step 1", "content": prompt_text.strip()}]

    total_steps = len(steps)
    result: list[dict[str, str]] = []
    for index, chunk in enumerate(steps, start=1):
        chunk_text = "\n\n".join(chunk).strip()
        if index < total_steps:
            chunk_text = (
                f"{chunk_text}\n\n"
                f"Continue to the next prompt step when you're ready. "
                f"Request step {index + 1} of {total_steps} to keep going."
            )
        result.append(
            {
                "step": index,
                "title": f"Prompt step {index}",
                "content": chunk_text,
            }
        )
    return result


def build_final_prompt_metadata(
    result: dict,
    *,
    deep_thinking: bool,
    version: int | None = None,
    variation_hint: str | None = None,
) -> dict:
    sections = parse_prompt_document_sections(result.get("content", ""))
    prompt_steps = split_prompt_into_steps(sections["prompt"])
    metadata: dict = {
        "type": "final_prompt",
        "is_final": True,
        "model": result.get("model", ""),
        "token_usage": result.get("token_usage", 0),
        "deep_thinking": deep_thinking,
        "prompt_document": sections,
        "prompt_steps": prompt_steps,
        "prompt_step_count": len(prompt_steps),
        "is_step_split": len(prompt_steps) > 1,
        "continuation_hint": (
            f"This prompt is split into {len(prompt_steps)} parts. Continue to the next prompt step when you're ready."
            if len(prompt_steps) > 1
            else ""
        ),
    }
    if version is not None:
        metadata["version"] = version
    if variation_hint:
        metadata["variation_hint"] = variation_hint
    return metadata


def latest_final_prompt_message(chat: RequestChat) -> RequestChatMessage | None:
    for message in reversed(chat.messages):
        if message.metadata.get("is_final"):
            return message
    return None


def build_follow_up_answer_prompt(chat: RequestChat, user_question: str) -> str:
    final_message = latest_final_prompt_message(chat)
    final_prompt_content = final_message.content if final_message else ""
    return (
        f"{build_generation_context(chat)}\n\n"
        "Latest generated final prompt:\n"
        f"{final_prompt_content}\n\n"
        "User follow-up question:\n"
        f"{user_question.strip()}\n"
    )


def build_follow_up_answer_system_prompt() -> str:
    return (
        "You are Thynk's prompt support assistant. The user already has a generated prompt and is now asking a follow-up question about it. "
        "Answer directly, clearly, and professionally. Focus on helping them understand, adapt, improve, or apply the generated prompt. "
        "Do not ask new intake-style clarification questions unless absolutely necessary. Do not generate a brand-new final prompt unless the user explicitly asks for one. "
        "Keep the response polished and structured. Format the answer in clean Markdown using only these sections when relevant: "
        "## Answer, ## Why, and ## Suggested next step. "
        "Use short bullets where useful, avoid fluff, and do not sound overly chatty."
    )


def chat_prefers_deep_thinking(chat: RequestChat) -> bool:
    for message in reversed(chat.messages):
        deep_thinking = message.metadata.get("deep_thinking")
        if isinstance(deep_thinking, bool):
            return deep_thinking
    return False


def build_prompt_generation_system_prompt(*, image_urls: list[str], deep_thinking: bool, is_regeneration: bool) -> str:
    base = (
        "You are Thynk's prompt generation engine. Your job is to produce a polished prompt that the user can paste into another AI tool. "
        "Do not complete the requested task yourself. Do not write the brief, plan, copy, design, code, strategy, or deliverable the user asked for. "
        "Instead, write the best possible prompt that instructs another AI to produce that deliverable. "
        "The prompt should be self-contained, production-ready, highly specific, and professionally structured. "
        "Anticipate missing requirements and convert them into explicit instructions, constraints, acceptance criteria, style direction, and output structure whenever the conversation supports it. "
        "Avoid placeholders unless the user clearly left something intentionally variable. "
    )
    if image_urls:
        base += (
            "Use the attached images as visual reference context and reflect their relevant layout, style, palette, brand cues, composition, or visual hierarchy when the conversation asks for it. "
        )
    if deep_thinking:
        base += (
            "Deep thinking mode is enabled. Think more comprehensively about scope, edge cases, implementation detail, quality bar, sequencing, and professional polish. "
            "Return a more extensive prompt with richer instruction depth, stronger context framing, clearer output requirements, and smarter constraints. "
        )
    else:
        base += (
            "Keep the prompt sharp and detailed, but do not over-expand beyond what materially improves quality. "
        )
    if is_regeneration:
        base += (
            "This is a regeneration, so produce meaningfully different framing, wording, or structure from earlier versions while staying high quality. "
        )
    base += (
        "Format the output as clean Markdown with these sections only: ## Prompt, ## Why this works, and ## Best used with. "
        "In ## Prompt, write a single paste-ready prompt in natural language that starts directly with the expert role or task framing, for example 'You are a senior UX designer...'. "
        "If the prompt becomes very long, organize it into clear sequential parts or phases so the user can continue step by step in another AI tool. "
        "Never answer the task directly; always output the prompt for another AI."
    )
    return base


async def create_chat(user: User, payload: RequestChatCreateRequest) -> RequestChatResponse:
    user_message = RequestChatMessage(
        id=uuid4().hex,
        role="user",
        content=payload.message,
        metadata={"image_urls": payload.image_urls or [], "deep_thinking": payload.deep_thinking},
        token_usage=0,
        model_used=None,
        created_at=utc_now(),
    )
    chat = RequestChat(
        user_id=user.id,
        title=payload.title,
        category=payload.category,
        source=payload.source,
        messages=[user_message],
    )

    clarification = await generate_clarification_for_chat(chat)
    assistant_message = create_assistant_clarification_message(clarification)
    chat.messages.append(assistant_message)
    await chat.insert()
    return serialize_chat(chat)


async def list_chats(user: User) -> list[RequestChatResponse]:
    chats = await RequestChat.find(RequestChat.user_id == user.id, RequestChat.deleted_at == None).sort("-updated_at").to_list()
    return [serialize_chat(chat) for chat in chats]


async def get_chat(user: User, chat_id: str) -> RequestChatResponse:
    chat = await RequestChat.get(chat_id)
    if not chat:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)
    if chat.user_id != user.id and user.role.value != "SUPER_ADMIN":
        raise AppException(403, "Request chat access denied.", ErrorCodes.CHAT_ACCESS_DENIED)
    return serialize_chat(chat)


async def add_message(user: User, chat_id: str, payload: RequestChatMessagePayload) -> RequestChatResponse:
    from app.services.ai.base import get_ai_service

    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)

    user_message = RequestChatMessage(
        id=uuid4().hex,
        role="user",
        content=payload.content,
        metadata={"image_urls": payload.image_urls or [], "deep_thinking": payload.deep_thinking},
        token_usage=0,
        model_used=None,
        created_at=utc_now(),
    )
    chat.messages.append(user_message)
    if latest_final_prompt_message(chat):
        ai_service = get_ai_service()
        image_urls = collect_all_image_urls(chat)
        images = [{"image_url": url, "detail": "auto"} for url in image_urls]
        result = await ai_service.generate_prompt(
            prompt=build_follow_up_answer_prompt(chat, payload.content),
            images=images if images else None,
            system_prompt=build_follow_up_answer_system_prompt(),
        )
        assistant_message = RequestChatMessage(
            id=uuid4().hex,
            role="assistant",
            content=result.get("content", "").strip(),
            metadata={
                "type": "follow_up_answer",
                "deep_thinking": payload.deep_thinking,
            },
            token_usage=result.get("token_usage"),
            model_used=result.get("model"),
            created_at=utc_now(),
        )
    else:
        clarification = await generate_clarification_for_chat(chat)
        assistant_message = create_assistant_clarification_message(clarification)
    chat.messages.append(assistant_message)
    chat.updated_at = utc_now()
    await chat.save()
    return serialize_chat(chat)


async def generate_final_prompt(user: User, chat_id: str, deep_thinking: bool = False) -> RequestChatResponse:
    from app.services.ai.base import get_ai_service

    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)

    await usage_tracker.ensure_generation_allowed(user)
    ai_service = get_ai_service()
    image_urls = collect_all_image_urls(chat)
    images = [{"image_url": url, "detail": "auto"} for url in image_urls]
    effective_deep_thinking = deep_thinking or chat_prefers_deep_thinking(chat)
    result = await ai_service.generate_prompt(
        prompt=build_generation_context(chat),
        images=images if images else None,
        system_prompt=build_prompt_generation_system_prompt(
            image_urls=image_urls,
            deep_thinking=effective_deep_thinking,
            is_regeneration=False,
        ),
    )

    assistant_message = RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=result.get("content", ""),
        metadata=build_final_prompt_metadata(result, deep_thinking=effective_deep_thinking),
        token_usage=result.get("token_usage"),
        model_used=result.get("model"),
        created_at=utc_now(),
    )
    chat.messages.append(assistant_message)
    chat.updated_at = utc_now()
    await chat.save()
    return serialize_chat(chat)


async def regenerate_prompt(user: User, chat_id: str, variation_hint: str | None = None, deep_thinking: bool = False) -> RequestChatResponse:
    from app.services.ai.base import get_ai_service

    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)

    variation_instruction = ""
    if variation_hint:
        variation_instruction = f"\n\nThe user has requested a variation with this direction: {variation_hint}. Incorporate this meaningfully."

    # Count existing final prompts for version labelling
    version = sum(1 for m in chat.messages if m.metadata.get("is_final")) + 1

    await usage_tracker.ensure_generation_allowed(user)
    ai_service = get_ai_service()
    image_urls = collect_all_image_urls(chat)
    images = [{"image_url": url, "detail": "auto"} for url in image_urls]
    effective_deep_thinking = deep_thinking or chat_prefers_deep_thinking(chat)
    result = await ai_service.generate_prompt(
        prompt=build_generation_context(chat) + variation_instruction,
        images=images if images else None,
        system_prompt=build_prompt_generation_system_prompt(
            image_urls=image_urls,
            deep_thinking=effective_deep_thinking,
            is_regeneration=True,
        ),
    )

    assistant_message = RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=result.get("content", ""),
        metadata=build_final_prompt_metadata(
            result,
            deep_thinking=effective_deep_thinking,
            version=version,
            variation_hint=variation_hint or "",
        ),
        token_usage=result.get("token_usage"),
        model_used=result.get("model"),
        created_at=utc_now(),
    )
    chat.messages.append(assistant_message)
    chat.updated_at = utc_now()
    await chat.save()
    return serialize_chat(chat)


async def update_chat(user: User, chat_id: str, payload: RequestChatUpdateRequest) -> RequestChatResponse:
    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(chat, key, value)
    await chat.save()
    return serialize_chat(chat)


async def delete_chat(user: User, chat_id: str) -> None:
    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)
    chat.deleted_at = utc_now()
    chat.status = "deleted"
    await chat.save()


async def clear_chats(user: User) -> int:
    chats = await RequestChat.find(
        RequestChat.user_id == user.id,
        RequestChat.deleted_at == None,
    ).to_list()
    if not chats:
        return 0

    deleted_at = utc_now()
    for chat in chats:
        chat.deleted_at = deleted_at
        chat.status = "deleted"
        await chat.save()

    return len(chats)


async def favorite_chat(user: User, chat_id: str) -> RequestChatResponse:
    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)
    chat.is_favorite = not chat.is_favorite
    await chat.save()
    return serialize_chat(chat)


async def report_chat(user: User, chat_id: str, payload: ReportChatRequest) -> RequestChatResponse:
    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)
    chat.is_reported = True
    chat.reported_reason = payload.reason
    await chat.save()
    return serialize_chat(chat)
