from app.api.v1.common import UserResponse
from app.api.v1.payments.service import reconcile_user_billing_state
from app.api.v1.users.schemas import UpdateProfileRequest
from app.models.usage_credit import UsageCredit
from app.models.user import User
from app.services.notifications.notification_service import NotificationService
from app.services.ai.usage_tracker import UsageTracker
from app.utils.datetime import ensure_utc, utc_now

usage_tracker = UsageTracker()
notification_service = NotificationService()


async def get_remaining_credits(user_id: str) -> int:
    credits = await UsageCredit.find(UsageCredit.user_id == user_id).to_list()
    now = utc_now()
    total = 0
    for credit in credits:
        if credit.expires_at and ensure_utc(credit.expires_at) < now:
            continue
        total += max(credit.remaining, 0)
    return total


async def serialize_user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(
        {
            **user.model_dump(),
            "credits_remaining": await get_remaining_credits(user.id),
        }
    )


async def get_profile(user: User) -> UserResponse:
    await usage_tracker.sync_usage_window(user)
    user, _, _ = await reconcile_user_billing_state(user)
    await notification_service.ensure_subscription_notifications(user)
    await notification_service.ensure_usage_notifications(user)
    return await serialize_user_response(user)


async def update_profile(user: User, payload: UpdateProfileRequest) -> UserResponse:
    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    await user.save()
    return await serialize_user_response(user)


async def soft_delete_user(user: User) -> None:
    from app.utils.datetime import utc_now

    user.deleted_at = utc_now()
    user.is_active = False
    await user.save()
