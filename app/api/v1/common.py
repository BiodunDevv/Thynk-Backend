from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import SubscriptionStatus, UserRole

T = TypeVar("T")


class UserResponse(BaseModel):
    id: str
    full_name: str = Field(description="User's full name.", examples=["Clinton Kehinde"])
    email: EmailStr
    role: UserRole
    is_verified: bool
    is_active: bool
    avatar_url: str | None = None
    current_plan_id: str | None = None
    subscription_status: SubscriptionStatus
    subscription_id: str | None = None
    prompt_generation_count: int
    monthly_generation_count: int
    credits_remaining: int = 0


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthPayload(BaseModel):
    tokens: TokenPair
    user: UserResponse
    role: UserRole
    plan: dict = Field(default_factory=dict)
    subscription_status: SubscriptionStatus


class MessageResponse(BaseModel):
    id: str | None = None
