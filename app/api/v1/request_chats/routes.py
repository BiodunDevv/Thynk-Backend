from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.request_chats.schemas import (
    ReportChatRequest,
    RequestChatCreateRequest,
    RequestChatMessagePayload,
    RequestChatRegenerateRequest,
    RequestChatResponse,
    RequestChatUpdateRequest,
)
from app.api.v1.request_chats.service import add_message, create_chat, delete_chat, favorite_chat, generate_final_prompt, get_chat, list_chats, regenerate_prompt, report_chat, update_chat
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/request-chats", tags=["Request Chats"])


@router.post("", response_model=SuccessResponse[RequestChatResponse], summary="Create request chat", description="Starts a new request chat for prompt or assistant history.")
async def create_request_chat(payload: RequestChatCreateRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chat created successfully.", data=await create_chat(user, payload))


@router.get("/me", response_model=SuccessResponse[list[RequestChatResponse]], summary="List request chats", description="Returns the logged-in user's request chat history.")
async def my_request_chats(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chats fetched successfully.", data=await list_chats(user))


@router.get("/{chat_id}", response_model=SuccessResponse[RequestChatResponse], summary="Get request chat", description="Returns a single request chat.")
async def read_request_chat(chat_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chat fetched successfully.", data=await get_chat(user, chat_id))


@router.post("/{chat_id}/messages", response_model=SuccessResponse[RequestChatResponse], summary="Add message to request chat", description="Adds a new user message to an existing request chat.")
async def append_message(chat_id: str, payload: RequestChatMessagePayload, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chat updated successfully.", data=await add_message(user, chat_id, payload))


@router.patch("/{chat_id}", response_model=SuccessResponse[RequestChatResponse], summary="Update request chat", description="Updates request chat title or status.")
async def patch_chat(chat_id: str, payload: RequestChatUpdateRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chat updated successfully.", data=await update_chat(user, chat_id, payload))


@router.delete("/{chat_id}", response_model=SuccessResponse[dict], summary="Delete request chat", description="Soft deletes a request chat.")
async def remove_chat(chat_id: str, user: User = Depends(get_current_user)):
    await delete_chat(user, chat_id)
    return SuccessResponse(message="Request chat deleted successfully.", data={})


@router.post("/{chat_id}/favorite", response_model=SuccessResponse[RequestChatResponse], summary="Favorite request chat", description="Marks or unmarks a request chat as favorite.")
async def toggle_favorite(chat_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chat favorite updated successfully.", data=await favorite_chat(user, chat_id))


@router.post("/{chat_id}/generate", response_model=SuccessResponse[RequestChatResponse], summary="Generate final prompt", description="Generates the final polished prompt from the conversation history.")
async def generate_final(chat_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Final prompt generated successfully.", data=await generate_final_prompt(user, chat_id))


@router.post("/{chat_id}/regenerate", response_model=SuccessResponse[RequestChatResponse], summary="Regenerate final prompt", description="Generates a new variation of the final prompt, optionally guided by a variation hint.")
async def regenerate_final(chat_id: str, payload: RequestChatRegenerateRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Prompt regenerated successfully.", data=await regenerate_prompt(user, chat_id, payload.variation_hint))


@router.post("/{chat_id}/report", response_model=SuccessResponse[RequestChatResponse], summary="Report bad AI response", description="Reports a request chat for admin review.")
async def report_request_chat(chat_id: str, payload: ReportChatRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Request chat reported successfully.", data=await report_chat(user, chat_id, payload))
