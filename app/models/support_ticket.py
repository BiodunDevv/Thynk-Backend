from datetime import datetime

from app.core.constants import SupportPriority, SupportTicketCategory, SupportTicketStatus
from pydantic import Field

from app.models.base import TimestampedDocument


class SupportTicket(TimestampedDocument):
    ticket_number: str
    user_id: str | None = None
    email: str
    full_name: str
    subject: str
    category: SupportTicketCategory
    priority: SupportPriority = SupportPriority.NORMAL
    status: SupportTicketStatus = SupportTicketStatus.OPEN
    assigned_admin_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    last_message_at: datetime | None = None
    closed_at: datetime | None = None

    class Settings:
        name = "support_tickets"
        indexes = ["ticket_number", "user_id", "status", "priority", "created_at"]
