from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.subscriptions.schemas import SubscriptionResponse
from app.api.v1.subscriptions.service import get_my_subscription
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/me", response_model=SuccessResponse[SubscriptionResponse | None], summary="Get my subscription", description="Returns the logged-in user's current subscription.")
async def my_subscription(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Subscription fetched successfully.", data=await get_my_subscription(user))
