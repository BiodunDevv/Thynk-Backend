from hashlib import sha256
from random import randint

from app.core.config import get_settings


class OTPService:
    def generate_code(self) -> str:
        settings = get_settings()
        return "".join(str(randint(0, 9)) for _ in range(settings.otp_length))

    def hash_code(self, code: str) -> str:
        return sha256(code.encode("utf-8")).hexdigest()
