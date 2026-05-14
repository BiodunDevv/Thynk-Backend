from app.core.config import get_settings
from app.core.constants import SubscriptionStatus, UserRole
from app.core.security import hash_password
from app.models.user import User
from app.utils.validators import normalize_email


async def seed_super_admin() -> None:
    settings = get_settings()
    if not settings.super_admin_email or not settings.super_admin_password or not settings.super_admin_name:
        return
    email = normalize_email(settings.super_admin_email)
    exists = await User.find_one(User.email == email)
    if exists:
        return
    user = User(
        full_name=settings.super_admin_name,
        email=email,
        password_hash=hash_password(settings.super_admin_password),
        role=UserRole.SUPER_ADMIN,
        is_verified=True,
        subscription_status=SubscriptionStatus.ACTIVE,
    )
    await user.insert()
