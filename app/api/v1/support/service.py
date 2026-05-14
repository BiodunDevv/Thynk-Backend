from app.api.v1.support.schemas import SupportReplyRequest, SupportTicketCreateRequest, SupportTicketResponse
from app.core.constants import NotificationType, SupportTicketStatus
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.support_activity import SupportActivity
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.services.email.email_service import EmailService
from app.services.push.push_service import PushService
from app.utils.datetime import utc_now
from app.utils.ids import generate_ticket_number

email_service = EmailService()
push_service = PushService()


def serialize_ticket(ticket: SupportTicket) -> SupportTicketResponse:
    return SupportTicketResponse.model_validate(ticket.model_dump())


async def create_ticket(user: User | None, payload: SupportTicketCreateRequest) -> SupportTicketResponse:
    ticket = SupportTicket(
        ticket_number=generate_ticket_number(),
        user_id=user.id if user else None,
        email=payload.email,
        full_name=payload.full_name,
        subject=payload.subject,
        category=payload.category,
        priority=payload.priority,
        last_message_at=utc_now(),
    )
    await ticket.insert()
    await SupportMessage(ticket_id=ticket.id, sender_id=user.id if user else None, sender_type="user", message=payload.message).insert()
    await SupportActivity(ticket_id=ticket.id, actor_id=user.id if user else None, actor_type="user", action="ticket_created").insert()
    await email_service.send_support_ticket_created(ticket.email, ticket.full_name, ticket.ticket_number)
    return serialize_ticket(ticket)


async def list_my_tickets(user: User) -> list[SupportTicketResponse]:
    tickets = await SupportTicket.find(SupportTicket.user_id == user.id).sort("-created_at").to_list()
    return [serialize_ticket(ticket) for ticket in tickets]


async def get_ticket_for_user(user: User, ticket_id: str) -> SupportTicketResponse:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket or ticket.user_id != user.id:
        raise AppException(404, "Support ticket not found.", ErrorCodes.SUPPORT_TICKET_NOT_FOUND)
    return serialize_ticket(ticket)


async def reply_to_ticket(user: User, ticket_id: str, payload: SupportReplyRequest) -> SupportTicketResponse:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket or ticket.user_id != user.id:
        raise AppException(404, "Support ticket not found.", ErrorCodes.SUPPORT_TICKET_NOT_FOUND)
    if ticket.status == SupportTicketStatus.CLOSED:
        raise AppException(400, "This support ticket is closed and cannot receive new replies.", ErrorCodes.SUPPORT_TICKET_CLOSED, details={"ticket_id": ticket.id, "status": ticket.status.value})
    ticket.status = SupportTicketStatus.PENDING_ADMIN if ticket.status != SupportTicketStatus.RESOLVED else SupportTicketStatus.PENDING_ADMIN
    ticket.last_message_at = utc_now()
    await ticket.save()
    await SupportMessage(ticket_id=ticket.id, sender_id=user.id, sender_type="user", message=payload.message).insert()
    await SupportActivity(ticket_id=ticket.id, actor_id=user.id, actor_type="user", action="user_replied").insert()
    return serialize_ticket(ticket)


async def close_ticket(user: User, ticket_id: str) -> SupportTicketResponse:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket or ticket.user_id != user.id:
        raise AppException(404, "Support ticket not found.", ErrorCodes.SUPPORT_TICKET_NOT_FOUND)
    ticket.status = SupportTicketStatus.CLOSED
    ticket.closed_at = utc_now()
    await ticket.save()
    return serialize_ticket(ticket)


async def reopen_ticket(user: User, ticket_id: str) -> SupportTicketResponse:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket or ticket.user_id != user.id:
        raise AppException(404, "Support ticket not found.", ErrorCodes.SUPPORT_TICKET_NOT_FOUND)
    ticket.status = SupportTicketStatus.PENDING_ADMIN
    ticket.closed_at = None
    await ticket.save()
    return serialize_ticket(ticket)
