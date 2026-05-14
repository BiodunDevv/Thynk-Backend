from datetime import timedelta

from app.core.config import get_settings
from app.core.security import create_token, hash_token


class TokenService:
    def create_access_token(self, user_id: str) -> str:
        settings = get_settings()
        return create_token(user_id, timedelta(minutes=settings.access_token_expire_minutes))

    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        settings = get_settings()
        token = create_token(user_id, timedelta(days=settings.refresh_token_expire_days), refresh=True)
        return token, hash_token(token)
