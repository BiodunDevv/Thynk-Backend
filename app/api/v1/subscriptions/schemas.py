from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: str
    provider: str
