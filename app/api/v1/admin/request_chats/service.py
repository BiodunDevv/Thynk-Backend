from app.api.v1.admin.request_chats.schemas import (
    AdminNoteRequest,
    AdminRequestChatOutputResponse,
    AdminRequestChatResponse,
    ConvertToTemplateRequest,
)
from app.models.audit_log import AuditLog
from app.models.prompt_template import PromptTemplate
from app.models.request_chat import RequestChat
from app.models.template_conversion import TemplateConversion
from app.models.user import User
from app.utils.validators import sanitize_template_content


def _serialize_admin_request_chat(chat: RequestChat) -> AdminRequestChatResponse:
    final_outputs = [
        AdminRequestChatOutputResponse(
            id=message.id,
            content=message.metadata.get("prompt_document", {}).get("prompt")
            if isinstance(message.metadata.get("prompt_document"), dict)
            and message.metadata.get("prompt_document", {}).get("prompt")
            else message.content,
            created_at=message.created_at.isoformat() if message.created_at else None,
            model_used=message.model_used,
            token_usage=message.token_usage,
        )
        for message in chat.messages
        if message.role == "assistant" and message.metadata.get("is_final")
    ]
    latest_output_preview = final_outputs[-1].content[:160] if final_outputs else None
    return AdminRequestChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        title=chat.title,
        category=chat.category,
        status=chat.status,
        is_reported=chat.is_reported,
        created_at=chat.created_at.isoformat() if chat.created_at else None,
        updated_at=chat.updated_at.isoformat() if chat.updated_at else None,
        generated_prompt_count=len(final_outputs),
        message_count=len(chat.messages),
        latest_output_preview=latest_output_preview,
        final_outputs=final_outputs,
    )


async def list_admin_request_chats() -> list[AdminRequestChatResponse]:
    chats = await RequestChat.find_all().sort("-created_at").to_list()
    return [_serialize_admin_request_chat(chat) for chat in chats]


async def get_admin_request_chat(chat_id: str) -> AdminRequestChatResponse | None:
    chat = await RequestChat.get(chat_id)
    return _serialize_admin_request_chat(chat) if chat else None


async def add_admin_note(admin: User, chat_id: str, payload: AdminNoteRequest) -> dict:
    chat = await RequestChat.get(chat_id)
    chat.admin_notes.append(payload.note)
    await chat.save()
    await AuditLog(actor_id=admin.id, actor_role=admin.role.value, action="admin_request_chat_note", entity_type="request_chat", entity_id=chat_id, new_value={"note": payload.note}).insert()
    return {"chat_id": chat_id, "note": payload.note}


async def convert_request_chat(admin: User, chat_id: str, payload: ConvertToTemplateRequest) -> dict:
    chat = await RequestChat.get(chat_id)
    sanitized = sanitize_template_content(payload.template_content)
    template = PromptTemplate(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        tags=payload.tags,
        is_premium=payload.is_premium,
        is_active=payload.is_active,
        template_content=sanitized,
    )
    await template.insert()
    conversion = TemplateConversion(
        source_chat_id=chat_id,
        source_user_id=chat.user_id,
        created_by_admin_id=admin.id,
        template_id=template.id,
        original_content_snapshot="\n".join(message.content for message in chat.messages),
        sanitized_content=sanitized,
        conversion_status="published" if payload.is_active else "draft",
        admin_notes=payload.admin_notes,
    )
    await conversion.insert()
    await AuditLog(actor_id=admin.id, actor_role=admin.role.value, action="convert_request_chat_to_template", entity_type="request_chat", entity_id=chat_id, new_value={"template_id": template.id}).insert()
    return {"template_id": template.id, "conversion_id": conversion.id, "status": conversion.conversion_status}
