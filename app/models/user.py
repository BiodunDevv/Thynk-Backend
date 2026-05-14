from datetime import datetime

from beanie import Indexed
from pydantic import EmailStr, Field

from app.core.constants import SubscriptionStatus, UserRole
from app.models.base import TimestampedDocument


class User(TimestampedDocument):
    full_name: str = Field(min_length=2, max_length=100)
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    role: UserRole = UserRole.USER
    is_verified: bool = False
    is_active: bool = True
    avatar_url: str | None = None
    expo_push_tokens: list[str] = Field(default_factory=list)
    current_plan_id: str | None = None
    subscription_status: SubscriptionStatus = SubscriptionStatus.FREE
    subscription_id: str | None = None
    prompt_generation_count: int = 0
    monthly_generation_count: int = 0
    last_generation_reset_at: datetime | None = None
    refresh_token_hash: str | None = None
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    deleted_at: datetime | None = None

    class Settings:
        name = "users"
