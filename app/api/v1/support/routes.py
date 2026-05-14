from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.support.schemas import SupportReplyRequest, SupportTicketCreateRequest, SupportTicketResponse
from app.api.v1.support.service import close_ticket, create_ticket, get_ticket_for_user, list_my_tickets, reopen_ticket, reply_to_ticket
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets", response_model=SuccessResponse[SupportTicketResponse], summary="Create support ticket", description="Creates a new support ticket for the current user.")
async def create_support_ticket(payload: SupportTicketCreateRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Support ticket created successfully.", data=await create_ticket(user, payload))


@router.get("/tickets/me", response_model=SuccessResponse[list[SupportTicketResponse]], summary="List my support tickets", description="Returns the current user's support tickets.")
async def my_support_tickets(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Support tickets fetched successfully.", data=await list_my_tickets(user))


@router.get("/tickets/{ticket_id}", response_model=SuccessResponse[SupportTicketResponse], summary="Get support ticket", description="Returns a single support ticket owned by the current user.")
async def get_support_ticket(ticket_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Support ticket fetched successfully.", data=await get_ticket_for_user(user, ticket_id))


@router.post("/tickets/{ticket_id}/reply", response_model=SuccessResponse[SupportTicketResponse], summary="Reply to support ticket", description="Adds a user reply to a support ticket.")
async def reply_support_ticket(ticket_id: str, payload: SupportReplyRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Support ticket updated successfully.", data=await reply_to_ticket(user, ticket_id, payload))


@router.patch("/tickets/{ticket_id}/close", response_model=SuccessResponse[SupportTicketResponse], summary="Close support ticket", description="Closes a support ticket.")
async def close_support_ticket(ticket_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Support ticket closed successfully.", data=await close_ticket(user, ticket_id))


@router.patch("/tickets/{ticket_id}/reopen", response_model=SuccessResponse[SupportTicketResponse], summary="Reopen support ticket", description="Reopens a resolved or closed ticket.")
async def reopen_support_ticket(ticket_id: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Support ticket reopened successfully.", data=await reopen_ticket(user, ticket_id))
