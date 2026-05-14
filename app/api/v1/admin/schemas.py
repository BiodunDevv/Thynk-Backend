from pydantic import BaseModel


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    paying_users: int
    total_prompts_generated: int
    open_support_tickets: int
    reported_request_chats: int
