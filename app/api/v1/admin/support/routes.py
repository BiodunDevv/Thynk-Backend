from fastapi import APIRouter, Depends

from app.api.v1.admin.support.schemas import (
    AdminReplyRequest,
    CannedReplyRequest,
    TicketAssignmentRequest,
    TicketPriorityRequest,
    TicketStatusRequest,
    TicketTagsRequest,
)
from app.api.v1.admin.support.service import add_internal_note, admin_reply, assign_ticket, create_canned_reply, get_activity, get_ticket, list_canned_replies, list_tickets, update_priority, update_status, update_tags
from app.api.v1.support.schemas import SupportTicketResponse
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/admin/support", tags=["Admin Support"])


@router.get("/tickets", response_model=SuccessResponse[list[SupportTicketResponse]], summary="List support tickets", description="Returns support tickets for the admin support desk. Requires Bearer token with SUPER_ADMIN role.")
async def admin_list_tickets(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support tickets fetched successfully.", data=await list_tickets())


@router.get("/tickets/{ticket_id}", response_model=SuccessResponse[SupportTicketResponse | None], summary="Get support ticket", description="Returns a support ticket for admin review.")
async def admin_get_ticket(ticket_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support ticket fetched successfully.", data=await get_ticket(ticket_id))


@router.post("/tickets/{ticket_id}/reply", response_model=SuccessResponse[dict], summary="Reply to support ticket", description="Sends an admin reply to a user support ticket.")
async def admin_ticket_reply(ticket_id: str, payload: AdminReplyRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support reply sent successfully.", data=await admin_reply(admin, ticket_id, payload))


@router.post("/tickets/{ticket_id}/internal-note", response_model=SuccessResponse[dict], summary="Add internal note", description="Adds an internal note that is not visible to the user.")
async def admin_internal_note(ticket_id: str, payload: AdminReplyRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Internal note added successfully.", data=await add_internal_note(admin, ticket_id, payload))


@router.patch("/tickets/{ticket_id}/assign", response_model=SuccessResponse[dict], summary="Assign support ticket", description="Assigns a support ticket to an admin.")
async def admin_assign(ticket_id: str, payload: TicketAssignmentRequest, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support ticket assigned successfully.", data=await assign_ticket(ticket_id, payload))


@router.patch("/tickets/{ticket_id}/priority", response_model=SuccessResponse[dict], summary="Update support ticket priority", description="Changes the support ticket priority.")
async def admin_change_priority(ticket_id: str, payload: TicketPriorityRequest, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support ticket priority updated successfully.", data=await update_priority(ticket_id, payload))


@router.patch("/tickets/{ticket_id}/status", response_model=SuccessResponse[dict], summary="Update support ticket status", description="Changes the support ticket status.")
async def admin_change_status(ticket_id: str, payload: TicketStatusRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support ticket status updated successfully.", data=await update_status(admin, ticket_id, payload))


@router.patch("/tickets/{ticket_id}/tags", response_model=SuccessResponse[dict], summary="Update support ticket tags", description="Updates support ticket tags.")
async def admin_change_tags(ticket_id: str, payload: TicketTagsRequest, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support ticket tags updated successfully.", data=await update_tags(ticket_id, payload))


@router.get("/tickets/{ticket_id}/activity", response_model=SuccessResponse[list[dict]], summary="Get ticket activity", description="Returns the full support ticket activity timeline.")
async def admin_ticket_activity(ticket_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Support ticket activity fetched successfully.", data=await get_activity(ticket_id))


@router.post("/canned-replies", response_model=SuccessResponse[dict], summary="Create canned reply", description="Creates a canned reply for faster admin support responses.")
async def admin_create_canned_reply(payload: CannedReplyRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Canned reply created successfully.", data=await create_canned_reply(admin, payload))


@router.get("/canned-replies", response_model=SuccessResponse[list[dict]], summary="List canned replies", description="Returns all canned replies.")
async def admin_list_canned_replies(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Canned replies fetched successfully.", data=await list_canned_replies())
