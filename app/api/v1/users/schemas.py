from pydantic import BaseModel, Field

from app.api.v1.common import UserResponse


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    avatar_url: str | None = None


class PushTokenRequest(BaseModel):
    token: str = Field(..., min_length=10, description="Device push token used for notification delivery.")
