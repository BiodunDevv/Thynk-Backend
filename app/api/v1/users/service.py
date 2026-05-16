from app.api.v1.common import UserResponse
from app.api.v1.payments.service import reconcile_user_billing_state
from app.api.v1.users.schemas import UpdateProfileRequest
from app.models.user import User
from app.services.notifications.notification_service import NotificationService
from app.services.ai.usage_tracker import UsageTracker

usage_tracker = UsageTracker()
notification_service = NotificationService()


async def get_profile(user: User) -> UserResponse:
    await usage_tracker.sync_usage_window(user)
    user, _, _ = await reconcile_user_billing_state(user)
    await notification_service.ensure_subscription_notifications(user)
    await notification_service.ensure_usage_notifications(user)
    return UserResponse.model_validate(user.model_dump())


async def update_profile(user: User, payload: UpdateProfileRequest) -> UserResponse:
    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    await user.save()
    return UserResponse.model_validate(user.model_dump())


async def soft_delete_user(user: User) -> None:
    from app.utils.datetime import utc_now

    user.deleted_at = utc_now()
    user.is_active = False
    await user.save()
