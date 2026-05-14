from pydantic import BaseModel


class AdminReplyRequest(BaseModel):
    message: str


class TicketAssignmentRequest(BaseModel):
    assigned_admin_id: str


class TicketPriorityRequest(BaseModel):
    priority: str


class TicketStatusRequest(BaseModel):
    status: str


class TicketTagsRequest(BaseModel):
    tags: list[str]


class CannedReplyRequest(BaseModel):
    title: str
    category: str
    body: str
    is_active: bool = True
