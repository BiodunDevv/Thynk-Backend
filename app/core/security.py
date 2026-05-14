from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_token(subject: str, expires_delta: timedelta, refresh: bool = False) -> str:
    settings = get_settings()
    secret = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": datetime.now(timezone.utc) + expires_delta,
        "type": "refresh" if refresh else "access",
    }
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, refresh: bool = False) -> dict[str, Any]:
    settings = get_settings()
    secret = settings.jwt_refresh_secret_key if refresh else settings.jwt_secret_key
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AppException(401, "Invalid token.", ErrorCodes.AUTH_TOKEN_INVALID) from exc
    expected_type = "refresh" if refresh else "access"
    if payload.get("type") != expected_type:
        raise AppException(401, "Invalid token type.", ErrorCodes.AUTH_TOKEN_INVALID)
    return payload
