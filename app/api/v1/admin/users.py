from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.common import UserResponse
from app.core.exceptions import AppException
from app.core.error_codes import ErrorCodes
from app.core.constants import UserRole
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.collection import Collection
from app.models.coupon import CouponRedemption
from app.models.notification import Notification
from app.models.otp import OTPCode
from app.models.payment import Payment, PaymentWebhookEvent
from app.models.prompt import Prompt
from app.models.request_chat import RequestChat
from app.models.subscription import Subscription
from app.models.support_activity import SupportActivity
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.template_conversion import TemplateConversion
from app.models.usage_credit import UsageCredit
from app.models.user import User
from app.services.ai.clarification_service import collect_all_image_urls
from app.api.v1.users.service import serialize_user_response
from app.services.notifications.notification_service import NotificationService
from app.core.constants import NotificationType
from app.utils.datetime import utc_now

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])
notification_service = NotificationService()


class GrantCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0)
    reason: str


class AdminUserOutputItem(BaseModel):
    id: str
    title: str
    category: str
    created_at: str | None = None
    generated_prompt_count: int
    final_outputs: list[str] = Field(default_factory=list)
    latest_output_preview: str | None = None
    status: str
    is_favorite: bool = False


class AdminDeleteUserResponse(BaseModel):
    id: str
    mode: str
    deleted_related_records: dict[str, int]


@router.get(
    "",
    response_model=SuccessResponse[list[UserResponse]],
    summary="List users",
    description="Returns all registered users for admin operations, including account status, verification state, active plan pointer, and prompt usage counters. Requires a SUPER_ADMIN bearer token.",
)
async def list_users(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    users = await User.find(User.role == UserRole.USER).sort("-created_at").to_list()
    serialized = [await serialize_user_response(user) for user in users]
    return SuccessResponse(message="Users fetched successfully.", data=serialized)


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    summary="Get user by ID",
    description="Returns a single user profile for the admin portal. Use this to inspect billing state, verification status, and usage counts before taking admin actions.",
)
async def get_user(user_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    return SuccessResponse(message="User fetched successfully.", data=await serialize_user_response(user))


@router.get(
    "/{user_id}/chats",
    response_model=SuccessResponse[list[AdminUserOutputItem]],
    summary="List a user's final outputs",
    description="Returns an admin-safe view of a user's request-chat history. Only final assistant outputs are exposed for operational review; raw drafting messages and full private conversations are intentionally excluded.",
)
async def list_user_chat_outputs(user_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)

    chats = await RequestChat.find(RequestChat.user_id == user_id).sort("-updated_at", "-created_at").to_list()
    items: list[AdminUserOutputItem] = []
    for chat in chats:
        final_outputs = [
            message.metadata.get("prompt_document", {}).get("prompt") if isinstance(message.metadata.get("prompt_document"), dict) and message.metadata.get("prompt_document", {}).get("prompt") else message.content
            for message in chat.messages
            if message.role == "assistant" and message.metadata.get("is_final")
        ]
        latest_output = final_outputs[-1] if final_outputs else None
        items.append(
            AdminUserOutputItem(
                id=chat.id,
                title=chat.title,
                category=chat.category,
                created_at=chat.created_at.isoformat() if chat.created_at else None,
                generated_prompt_count=len(final_outputs),
                final_outputs=final_outputs,
                latest_output_preview=(latest_output[:280].strip() if latest_output else None),
                status=chat.status.value if hasattr(chat.status, "value") else str(chat.status),
                is_favorite=chat.is_favorite,
            )
        )

    return SuccessResponse(message="User final outputs fetched successfully.", data=items)


@router.patch(
    "/{user_id}/toggle-status",
    response_model=SuccessResponse[UserResponse],
    summary="Toggle user active status",
    description="Activates or deactivates a user account. This is intended for abuse handling, compliance review, and account recovery workflows. Requires a SUPER_ADMIN bearer token.",
)
async def toggle_user_status(user_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    user.is_active = not user.is_active
    await user.save()
    return SuccessResponse(message=f"User {'activated' if user.is_active else 'deactivated'} successfully.", data=await serialize_user_response(user))


@router.patch(
    "/{user_id}/deactivate",
    response_model=SuccessResponse[UserResponse],
    summary="Deactivate user account",
    description="Soft-deactivates a user account for moderation, fraud review, or compliance reasons. The user record is retained, the account is marked inactive, and the deleted timestamp is set for audit visibility.",
)
async def deactivate_user(user_id: str, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    if admin.id == user_id:
        raise AppException(400, "You cannot deactivate your own admin account.", ErrorCodes.ADMIN_ACTION_NOT_ALLOWED)
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    user.is_active = False
    user.deleted_at = utc_now()
    await user.save()
    return SuccessResponse(message="User deactivated successfully.", data=await serialize_user_response(user))


@router.patch(
    "/{user_id}/reactivate",
    response_model=SuccessResponse[UserResponse],
    summary="Reactivate user account",
    description="Restores a previously deactivated user account by marking it active again and clearing the deleted timestamp.",
)
async def reactivate_user(user_id: str, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    if admin.id == user_id:
        raise AppException(400, "You cannot reactivate your own admin account through this action.", ErrorCodes.ADMIN_ACTION_NOT_ALLOWED)
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    user.is_active = True
    user.deleted_at = None
    await user.save()
    return SuccessResponse(message="User reactivated successfully.", data=await serialize_user_response(user))


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse[AdminDeleteUserResponse],
    summary="Delete user account permanently",
    description="Permanently removes a user account and deletes user-owned application records including prompts, chats, payments, webhook traces, notifications, credits, subscriptions, coupon redemptions, OTP records, support history, and conversion artifacts.",
)
async def delete_user(user_id: str, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    if admin.id == user_id:
        raise AppException(400, "You cannot delete your own admin account.", ErrorCodes.ADMIN_ACTION_NOT_ALLOWED)
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)

    deleted_counts = {
        "prompts": 0,
        "request_chats": 0,
        "usage_credits": 0,
        "notifications": 0,
        "subscriptions": 0,
        "support_tickets": 0,
        "support_messages": 0,
        "support_activities": 0,
        "payments": 0,
        "payment_webhook_events": 0,
        "collections": 0,
        "coupon_redemptions": 0,
        "template_conversions": 0,
        "otp_codes": 0,
    }

    payments = await Payment.find(Payment.user_id == user_id).to_list()
    payment_ids = [payment.id for payment in payments]
    payment_references = [payment.provider_reference for payment in payments if payment.provider_reference]
    for payment in payments:
        await payment.delete()
    deleted_counts["payments"] = len(payments)

    webhook_events = []
    if payment_ids or payment_references:
        filters = []
        if payment_ids:
            filters.append({"payment_id": {"$in": payment_ids}})
        if payment_references:
            filters.append({"provider_reference": {"$in": payment_references}})
        webhook_events = await PaymentWebhookEvent.find({"$or": filters}).to_list()
        for event in webhook_events:
            await event.delete()
    deleted_counts["payment_webhook_events"] = len(webhook_events)

    prompts = await Prompt.find(Prompt.user_id == user_id).to_list()
    for prompt in prompts:
        await prompt.delete()
    deleted_counts["prompts"] = len(prompts)

    chats = await RequestChat.find(RequestChat.user_id == user_id).to_list()
    for chat in chats:
        await chat.delete()
    deleted_counts["request_chats"] = len(chats)

    collections = await Collection.find(Collection.user_id == user_id).to_list()
    for collection in collections:
        await collection.delete()
    deleted_counts["collections"] = len(collections)

    credits = await UsageCredit.find(UsageCredit.user_id == user_id).to_list()
    for credit in credits:
        await credit.delete()
    deleted_counts["usage_credits"] = len(credits)

    notifications = await Notification.find(Notification.user_id == user_id).to_list()
    for notification in notifications:
        await notification.delete()
    deleted_counts["notifications"] = len(notifications)

    subscriptions = await Subscription.find(Subscription.user_id == user_id).to_list()
    for subscription in subscriptions:
        await subscription.delete()
    deleted_counts["subscriptions"] = len(subscriptions)

    coupon_redemptions = await CouponRedemption.find(CouponRedemption.user_id == user_id).to_list()
    for redemption in coupon_redemptions:
        await redemption.delete()
    deleted_counts["coupon_redemptions"] = len(coupon_redemptions)

    template_conversions = await TemplateConversion.find(TemplateConversion.source_user_id == user_id).to_list()
    for conversion in template_conversions:
        await conversion.delete()
    deleted_counts["template_conversions"] = len(template_conversions)

    otp_codes = await OTPCode.find(OTPCode.email == user.email).to_list()
    for otp_code in otp_codes:
        await otp_code.delete()
    deleted_counts["otp_codes"] = len(otp_codes)

    tickets = await SupportTicket.find(
        {
            "$or": [
                {"user_id": user_id},
                {"email": user.email},
            ]
        }
    ).to_list()
    ticket_ids = [ticket.id for ticket in tickets]
    if ticket_ids:
        messages = await SupportMessage.find({"ticket_id": {"$in": ticket_ids}}).to_list()
        for message in messages:
            await message.delete()
        deleted_counts["support_messages"] = len(messages)

        activities = await SupportActivity.find({"ticket_id": {"$in": ticket_ids}}).to_list()
        for activity in activities:
            await activity.delete()
        deleted_counts["support_activities"] = len(activities)

    for ticket in tickets:
        await ticket.delete()
    deleted_counts["support_tickets"] = len(tickets)

    await user.delete()

    return SuccessResponse(
        message="User account deleted successfully.",
        data=AdminDeleteUserResponse(id=user_id, mode="hard_delete", deleted_related_records=deleted_counts),
    )


@router.post(
    "/{user_id}/grant-credits",
    response_model=SuccessResponse[dict],
    summary="Grant AI usage credits",
    description="Creates an admin-granted usage credit record for the selected user. Use this for goodwill adjustments, incident recovery, or discretionary support actions.",
)
async def grant_credits(user_id: str, payload: GrantCreditsRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    credit = UsageCredit(user_id=user_id, source="admin_grant", amount=payload.amount, remaining=payload.amount, created_by_admin_id=admin.id)
    await credit.insert()
    await notification_service.create_notification(
        user,
        "Points added to your account",
        f"{payload.amount:,} points were added to your Thynk account by the support team.",
        NotificationType.ACCOUNT,
        data={
            "event": "admin_points_granted",
            "amount": payload.amount,
            "reason": payload.reason,
            "granted_by_admin_id": admin.id,
        },
        send_push=True,
    )
    return SuccessResponse(message="AI credits granted successfully.", data={"user_id": user_id, "credits_added": credit.amount, "remaining_credits": credit.remaining})


class GrantPromptsRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Number of extra prompt generations to grant")
    reason: str = Field(default="Admin grant")


@router.post(
    "/{user_id}/grant-prompts",
    response_model=SuccessResponse[dict],
    summary="Grant extra prompt generations directly",
    description="Grants extra prompt-generation allowance to a user through the admin portal. This is useful for support remediation and premium-service recovery flows.",
)
async def grant_prompts(user_id: str, payload: GrantPromptsRequest, admin: User = Depends(require_role(role="SUPER_ADMIN"))):
    user = await User.get(user_id)
    if not user or user.role != UserRole.USER:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    await notification_service.create_notification(
        user,
        "Extra prompt generations added",
        f"{payload.amount:,} extra prompt generations were added to your account.",
        NotificationType.USAGE,
        data={
            "event": "admin_prompt_grant",
            "amount": payload.amount,
            "reason": payload.reason,
            "granted_by_admin_id": admin.id,
        },
        send_push=True,
    )
    credit = UsageCredit(user_id=user_id, source="admin_grant", amount=payload.amount, remaining=payload.amount, created_by_admin_id=admin.id)
    await credit.insert()
    return SuccessResponse(
        message=f"{payload.amount} prompt generations granted.",
        data={"user_id": user_id, "prompts_granted": payload.amount, "monthly_count": user.monthly_generation_count},
    )


# ── Admin prompts router ────────────────────────────────────────────────────
prompts_router = APIRouter(prefix="/admin/prompts", tags=["Admin Prompts"])


@prompts_router.get(
    "",
    response_model=SuccessResponse[list[dict]],
    summary="List generated prompts",
    description="Returns admin-safe generated prompt records across both saved prompts and request-chat final outputs. Only the end product is exposed; raw user drafting conversations are intentionally excluded.",
)
async def list_all_prompts(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    prompts = await Prompt.find_all().sort("-created_at").to_list()
    chats = await RequestChat.find_all().to_list()
    user_ids = {
        *(prompt.user_id for prompt in prompts),
        *(chat.user_id for chat in chats),
    }
    users = [user for user in await User.find_all().to_list() if user.id in user_ids] if user_ids else []
    user_map = {user.id: user for user in users}

    normalized_prompts = [
        {
            **p.model_dump(mode="json"),
            "source": "saved_prompt",
            "user_name": user_map.get(p.user_id).full_name if user_map.get(p.user_id) else None,
            "user_email": user_map.get(p.user_id).email if user_map.get(p.user_id) else None,
        }
        for p in prompts
    ]

    chat_prompts: list[dict] = []
    for chat in chats:
        user = user_map.get(chat.user_id)
        for message in chat.messages:
            if message.role != "assistant" or not message.metadata.get("is_final"):
                continue
            prompt_document = message.metadata.get("prompt_document")
            generated_prompt = (
                prompt_document.get("prompt")
                if isinstance(prompt_document, dict) and prompt_document.get("prompt")
                else message.content
            )
            chat_prompts.append(
                {
                    "id": message.id,
                    "user_id": chat.user_id,
                    "title": chat.title,
                    "rough_input": None,
                    "generated_prompt": generated_prompt,
                    "category": chat.category,
                    "tone": None,
                    "platform": "request-chat",
                    "complexity": "deep" if message.metadata.get("deep_thinking") else "standard",
                    "output_format": "markdown",
                    "image_urls": collect_all_image_urls(chat),
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                    "source": "request_chat",
                    "user_name": user.full_name if user else None,
                    "user_email": user.email if user else None,
                }
            )

    combined = normalized_prompts + chat_prompts
    combined.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return SuccessResponse(
        message="Prompts fetched successfully.",
        data=combined,
    )
    coupon_redemptions = await CouponRedemption.find(CouponRedemption.user_id == user_id).to_list()
    for redemption in coupon_redemptions:
        await redemption.delete()
    deleted_counts["coupon_redemptions"] = len(coupon_redemptions)

    conversions = await TemplateConversion.find(TemplateConversion.source_user_id == user_id).to_list()
    for conversion in conversions:
        await conversion.delete()
    deleted_counts["template_conversions"] = len(conversions)
