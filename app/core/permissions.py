from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.constants import UserRole
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    if not credentials:
        raise AppException(401, "Authentication required.", ErrorCodes.AUTH_TOKEN_INVALID)
    payload = decode_token(credentials.credentials)
    user = await User.get(payload["sub"])
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    if user.deleted_at:
        raise AppException(403, "Account has been deleted.", ErrorCodes.USER_ACCOUNT_DELETED)
    if not user.is_active:
        raise AppException(403, "Account is disabled.", ErrorCodes.AUTH_ACCOUNT_DISABLED)
    return user


def require_role(role: UserRole | str):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        expected_role = role.value if isinstance(role, UserRole) else role
        if user.role.value != expected_role:
            raise AppException(403, "Admin only route.", ErrorCodes.ADMIN_ONLY_ROUTE)
        return user

    return dependency
