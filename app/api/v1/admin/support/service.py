from app.api.v1.admin.support.schemas import (
    AdminReplyRequest,
    CannedReplyRequest,
    TicketAssignmentRequest,
    TicketPriorityRequest,
    TicketStatusRequest,
    TicketTagsRequest,
)
from app.api.v1.support.schemas import SupportTicketResponse
from app.core.constants import NotificationType
from app.models.audit_log import AuditLog
from app.models.canned_reply import CannedReply
from app.models.support_activity import SupportActivity
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.services.email.email_service import EmailService
from app.services.push.push_service import PushService
from app.utils.datetime import utc_now

email_service = EmailService()
push_service = PushService()


async def list_tickets() -> list[SupportTicketResponse]:
    tickets = await SupportTicket.find_all().sort("-updated_at").to_list()
    return [SupportTicketResponse.model_validate(ticket.model_dump()) for ticket in tickets]


async def get_ticket(ticket_id: str) -> SupportTicketResponse | None:
    ticket = await SupportTicket.get(ticket_id)
    return SupportTicketResponse.model_validate(ticket.model_dump()) if ticket else None


async def admin_reply(admin: User, ticket_id: str, payload: AdminReplyRequest) -> dict:
    ticket = await SupportTicket.get(ticket_id)
    ticket.status = "pending_user"
    ticket.last_message_at = utc_now()
    await ticket.save()
    await SupportMessage(ticket_id=ticket.id, sender_id=admin.id, sender_type="admin", message=payload.message).insert()
    await SupportActivity(ticket_id=ticket.id, actor_id=admin.id, actor_type="admin", action="admin_replied").insert()
    await AuditLog(actor_id=admin.id, actor_role=admin.role.value, action="admin_support_reply", entity_type="support_ticket", entity_id=ticket.id).insert()
    if ticket.user_id:
        user = await User.get(ticket.user_id)
        if user:
            await email_service.send_support_ticket_reply(ticket.email, ticket.full_name, ticket.ticket_number, payload.message[:120])
            await push_service.notify_user(
                user,
                "Support replied to your ticket",
                "Our team has responded to your request.",
                NotificationType.SUPPORT,
                {"ticket_id": ticket.id, "url": "/support"},
            )
    return {"ticket_id": ticket.id}


async def add_internal_note(admin: User, ticket_id: str, payload: AdminReplyRequest) -> dict:
    await SupportMessage(ticket_id=ticket_id, sender_id=admin.id, sender_type="admin", message=payload.message, is_internal_note=True).insert()
    await SupportActivity(ticket_id=ticket_id, actor_id=admin.id, actor_type="admin", action="internal_note_added").insert()
    return {"ticket_id": ticket_id}


async def assign_ticket(ticket_id: str, payload: TicketAssignmentRequest) -> dict:
    ticket = await SupportTicket.get(ticket_id)
    ticket.assigned_admin_id = payload.assigned_admin_id
    await ticket.save()
    return {"ticket_id": ticket_id, "assigned_admin_id": payload.assigned_admin_id}


async def update_priority(ticket_id: str, payload: TicketPriorityRequest) -> dict:
    ticket = await SupportTicket.get(ticket_id)
    ticket.priority = payload.priority
    await ticket.save()
    return {"ticket_id": ticket_id, "priority": payload.priority}


async def update_status(admin: User, ticket_id: str, payload: TicketStatusRequest) -> dict:
    ticket = await SupportTicket.get(ticket_id)
    ticket.status = payload.status
    await ticket.save()
    await SupportActivity(ticket_id=ticket.id, actor_id=admin.id, actor_type="admin", action="status_changed", new_value=payload.status).insert()
    return {"ticket_id": ticket_id, "status": payload.status}


async def update_tags(ticket_id: str, payload: TicketTagsRequest) -> dict:
    ticket = await SupportTicket.get(ticket_id)
    ticket.tags = payload.tags
    await ticket.save()
    return {"ticket_id": ticket_id, "tags": payload.tags}


async def get_activity(ticket_id: str) -> list[dict]:
    activity = await SupportActivity.find(SupportActivity.ticket_id == ticket_id).sort("-created_at").to_list()
    return [item.model_dump() for item in activity]


async def create_canned_reply(admin: User, payload: CannedReplyRequest) -> dict:
    reply = CannedReply(**payload.model_dump(), created_by=admin.id)
    await reply.insert()
    return reply.model_dump()


async def list_canned_replies() -> list[dict]:
    return [item.model_dump() for item in await CannedReply.find_all().sort("-created_at").to_list()]
