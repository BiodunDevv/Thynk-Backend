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
from app.utils.datetime import utc_now


def serialize_chat(chat: RequestChat) -> RequestChatResponse:
    return RequestChatResponse.model_validate(chat.model_dump())


async def create_chat(user: User, payload: RequestChatCreateRequest) -> RequestChatResponse:
    from app.services.ai.base import get_ai_service

    user_message = RequestChatMessage(
        id=uuid4().hex,
        role="user",
        content=payload.message,
        metadata={},
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
    await chat.insert()

    ai_instruction = (
        "You are Thynk's AI assistant. A user just started a new chat. "
        f"Category: {payload.category}. Their opening message: {payload.message}\n\n"
        "Ask 1-2 targeted follow-up questions to understand their intent, audience, tone, "
        "and desired output format. Be concise and professional."
    )
    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(
        prompt=ai_instruction,
        system_prompt=(
            "You are Thynk's prompt refinement assistant. Ask clarifying questions. "
            "Be professional and concise. Never generate the final prompt yet."
        ),
    )
    assistant_message = RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=result.get("content", "To help you create the best prompt, could you share more about your target audience and the output format you need?"),
        metadata={"model": result.get("model", ""), "token_usage": result.get("token_usage", 0)},
        token_usage=result.get("token_usage"),
        model_used=result.get("model"),
        created_at=utc_now(),
    )
    chat.messages.append(assistant_message)
    await chat.save()
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
        metadata={},
        token_usage=0,
        model_used=None,
        created_at=utc_now(),
    )
    chat.messages.append(user_message)

    conversation_history = "\n".join(
        f"{m.role.upper()}: {m.content}" for m in chat.messages
    )

    ai_instruction = (
        "You are Thynk's AI assistant helping a user refine their prompt idea. "
        "Your job is to ask 1-2 focused follow-up questions to better understand their intent, "
        "context, audience, tone, or output format. Be concise, professional, and helpful. "
        "Do not generate the final prompt yet — only ask clarifying questions. "
        f"Conversation so far:\n{conversation_history}"
    )

    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(
        prompt=ai_instruction,
        system_prompt=(
            "You are Thynk's intelligent prompt refinement assistant. "
            "Ask targeted follow-up questions to gather what you need to build the best possible AI prompt. "
            "Keep responses under 3 sentences. Never generate the prompt unless explicitly asked."
        ),
    )

    assistant_message = RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=result.get("content", "Could you tell me more about what you're trying to achieve?"),
        metadata={"model": result.get("model", ""), "token_usage": result.get("token_usage", 0)},
        token_usage=result.get("token_usage"),
        model_used=result.get("model"),
        created_at=utc_now(),
    )
    chat.messages.append(assistant_message)
    chat.updated_at = utc_now()
    await chat.save()
    return serialize_chat(chat)


async def generate_final_prompt(user: User, chat_id: str) -> RequestChatResponse:
    from app.services.ai.base import get_ai_service

    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)

    conversation_history = "\n".join(
        f"{m.role.upper()}: {m.content}" for m in chat.messages
    )

    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(
        prompt=conversation_history,
        system_prompt=(
            "You are Thynk's prompt generation engine. Based on this conversation, generate the final polished AI prompt the user needs. "
            "Format it as clean Markdown with clear sections. Include a ## Prompt section with the actual prompt text, "
            "and a ## How to use section. Be thorough and professional."
        ),
    )

    assistant_message = RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=result.get("content", ""),
        metadata={"type": "final_prompt", "is_final": True, "model": result.get("model", ""), "token_usage": result.get("token_usage", 0)},
        token_usage=result.get("token_usage"),
        model_used=result.get("model"),
        created_at=utc_now(),
    )
    chat.messages.append(assistant_message)
    chat.updated_at = utc_now()
    await chat.save()
    return serialize_chat(chat)


async def regenerate_prompt(user: User, chat_id: str, variation_hint: str | None = None) -> RequestChatResponse:
    from app.services.ai.base import get_ai_service

    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)

    conversation_history = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in chat.messages
        if not m.metadata.get("is_final")
    )

    variation_instruction = ""
    if variation_hint:
        variation_instruction = f"\n\nThe user has requested a variation with this direction: {variation_hint}. Incorporate this meaningfully."

    # Count existing final prompts for version labelling
    version = sum(1 for m in chat.messages if m.metadata.get("is_final")) + 1

    ai_service = get_ai_service()
    result = await ai_service.generate_prompt(
        prompt=conversation_history + variation_instruction,
        system_prompt=(
            "You are Thynk's prompt generation engine. Based on this conversation, generate a fresh variation of the final polished AI prompt. "
            "This is a regeneration — produce meaningfully different wording, structure, or framing compared to any previous version. "
            "Format it as clean Markdown with clear sections: ## Prompt (the actual prompt text) and ## How to use. "
            "Be thorough and professional."
        ),
    )

    assistant_message = RequestChatMessage(
        id=uuid4().hex,
        role="assistant",
        content=result.get("content", ""),
        metadata={
            "type": "final_prompt",
            "is_final": True,
            "version": version,
            "variation_hint": variation_hint or "",
            "model": result.get("model", ""),
            "token_usage": result.get("token_usage", 0),
        },
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
