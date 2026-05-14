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
    chat = RequestChat(
        user_id=user.id,
        title=payload.title,
        category=payload.category,
        source=payload.source,
        messages=[RequestChatMessage(id=uuid4().hex, role="user", content=payload.message, metadata={}, token_usage=0, model_used=None, created_at=utc_now())],
    )
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
    chat = await RequestChat.get(chat_id)
    if not chat or chat.user_id != user.id:
        raise AppException(404, "Request chat not found.", ErrorCodes.CHAT_NOT_FOUND)
    chat.messages.append(RequestChatMessage(id=uuid4().hex, role="user", content=payload.content, metadata={}, token_usage=0, model_used=None, created_at=utc_now()))
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
