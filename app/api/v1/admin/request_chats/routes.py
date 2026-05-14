from fastapi import APIRouter, Depends

from app.api.v1.admin.request_chats.schemas import AdminNoteRequest, ConvertToTemplateRequest
from app.api.v1.admin.request_chats.service import add_admin_note, convert_request_chat, get_admin_request_chat, list_admin_request_chats
from app.api.v1.request_chats.schemas import RequestChatResponse
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/admin/request-chats", tags=["Admin Request Chats"])


@router.get("", response_model=SuccessResponse[list[RequestChatResponse]], summary="List request chats for admin review", description="Returns user request chats for product, support, and abuse review. Requires Bearer token with SUPER_ADMIN role.")
async def admin_list_request_chats(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Request chats fetched successfully.", data=await list_admin_request_chats())


@router.get("/{chat_id}", response_model=SuccessResponse[RequestChatResponse | None], summary="Get request chat for admin review", description="Returns a single request chat. Requires Bearer token with SUPER_ADMIN role.")
async def admin_get_request_chat(chat_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Request chat fetched successfully.", data=await get_admin_request_chat(chat_id))


@router.post("/{chat_id}/notes", response_model=SuccessResponse[dict], summary="Add internal admin note", description="Adds an internal admin note to a request chat.")
async def admin_note(chat_id: str, payload: AdminNoteRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Admin note added successfully.", data=await add_admin_note(admin, chat_id, payload))


@router.post("/{chat_id}/convert-to-template", response_model=SuccessResponse[dict], summary="Convert request chat to template", description="Creates a sanitized prompt template draft or published template from a user request chat.")
async def admin_convert(chat_id: str, payload: ConvertToTemplateRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Request chat converted to template draft successfully.", data=await convert_request_chat(admin, chat_id, payload))
