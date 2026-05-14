from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.core.constants import SupportPriority, SupportTicketCategory, SupportTicketStatus


class SupportTicketCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    subject: str
    category: SupportTicketCategory
    message: str
    priority: SupportPriority = SupportPriority.NORMAL


class SupportReplyRequest(BaseModel):
    message: str


class SupportTicketResponse(BaseModel):
    id: str
    ticket_number: str
    email: EmailStr
    full_name: str
    subject: str
    category: SupportTicketCategory
    priority: SupportPriority
    status: SupportTicketStatus
    assigned_admin_id: str | None = None
    tags: list[str]
    last_message_at: datetime | None = None
