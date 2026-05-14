from datetime import datetime

from pydantic import EmailStr

from app.core.constants import OtpPurpose
from app.models.base import TimestampedDocument


class OTPCode(TimestampedDocument):
    email: EmailStr
    code_hash: str
    purpose: OtpPurpose
    expires_at: datetime
    attempts: int = 0
    is_used: bool = False
    cooldown_until: datetime | None = None

    class Settings:
        name = "otp_codes"
