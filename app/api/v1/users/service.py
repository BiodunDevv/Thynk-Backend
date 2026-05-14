from app.api.v1.common import UserResponse
from app.api.v1.users.schemas import UpdateProfileRequest
from app.models.user import User


async def get_profile(user: User) -> UserResponse:
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
