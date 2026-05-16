from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.constants import NotificationType, SubscriptionStatus
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.notification import Notification
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.user import User
from app.services.push.push_service import PushService
from app.utils.datetime import ensure_utc, utc_now


class NotificationService:
    def __init__(self) -> None:
        self.push_service = PushService()

    @staticmethod
    def normalize_token(token: str) -> str:
        return token.strip()

    async def create_notification(
        self,
        user: User,
        title: str,
        body: str,
        kind: NotificationType,
        data: dict | None = None,
        *,
        dedupe_key: str | None = None,
        send_push: bool = False,
    ) -> Notification:
        if send_push:
            return await self.push_service.notify_user(
                user,
                title,
                body,
                kind,
                {"dedupe_key": dedupe_key, **(data or {})} if dedupe_key else (data or {}),
            )

        notification = Notification(
            user_id=user.id,
            title=title,
            body=body,
            type=kind,
            data=data or {},
            dedupe_key=dedupe_key,
        )
        await notification.insert()
        return notification

    async def create_notification_once(
        self,
        user: User,
        title: str,
        body: str,
        kind: NotificationType,
        dedupe_key: str,
        data: dict | None = None,
        *,
        send_push: bool = False,
    ) -> Notification | None:
        existing = await Notification.find_one(
            Notification.user_id == user.id,
            Notification.dedupe_key == dedupe_key,
        )
        if existing:
            return None

        payload = data or {}
        return await self.create_notification(
            user,
            title,
            body,
            kind,
            payload,
            dedupe_key=dedupe_key,
            send_push=send_push,
        )

    async def list_notifications(self, user: User) -> list[Notification]:
        return await Notification.find(Notification.user_id == user.id).sort("-created_at").to_list()

    async def mark_read(self, user: User, notification_id: str) -> Notification:
        notification = await Notification.get(notification_id)
        if not notification or notification.user_id != user.id:
            raise AppException(404, "Notification not found.", ErrorCodes.RESOURCE_NOT_FOUND)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = utc_now()
            await notification.save()
        return notification

    async def mark_all_read(self, user: User) -> int:
        notifications = await Notification.find(
            Notification.user_id == user.id,
            Notification.is_read == False,
        ).to_list()
        if not notifications:
            return 0

        now = utc_now()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            await notification.save()
        return len(notifications)

    async def send_test_notification(self, user: User) -> Notification:
        return await self.create_notification(
            user,
            "Thynk test notification",
            "Everything is connected correctly. Prompt, billing, and account alerts will appear here.",
            NotificationType.SYSTEM,
            {"event": "test_notification"},
            send_push=True,
        )

    async def get_summary(self, user: User) -> dict:
        unread = await Notification.find(
            Notification.user_id == user.id,
            Notification.is_read == False,
        ).count()
        return {
            "unread_count": unread,
            "registered_devices": len(user.expo_push_tokens),
            "has_browser_token": any(token.startswith("web:") for token in user.expo_push_tokens),
        }

    async def ensure_subscription_notifications(self, user: User) -> None:
        subscription = None
        if user.subscription_id:
            subscription = await Subscription.get(user.subscription_id)
        if not subscription:
            subscription = await Subscription.find_one(Subscription.user_id == user.id)
        if not subscription:
            return

        plan = await Plan.get(subscription.plan_id) if subscription.plan_id else None
        plan_name = plan.name if plan else "your plan"
        period_end = ensure_utc(subscription.current_period_end) if subscription.current_period_end else None

        if subscription.status == SubscriptionStatus.ACTIVE and period_end:
            now = datetime.now(timezone.utc)
            remaining_days = (period_end - now).days
            for threshold in (1, 3, 7):
                if 0 <= remaining_days <= threshold:
                    await self.create_notification_once(
                        user,
                        "Subscription renewal reminder",
                        f"{plan_name} renews in {remaining_days} day{'s' if remaining_days != 1 else ''}.",
                        NotificationType.BILLING,
                        dedupe_key=f"subscription_renewal:{subscription.id}:{threshold}:{period_end.date().isoformat()}",
                        data={
                            "event": "subscription_renewal_reminder",
                            "subscription_id": subscription.id,
                            "plan_id": subscription.plan_id,
                            "days_remaining": remaining_days,
                            "period_end": period_end.isoformat(),
                        },
                        send_push=remaining_days <= 3,
                    )
                    break

        if period_end and period_end < datetime.now(timezone.utc):
            await self.create_notification_once(
                user,
                "Subscription ended",
                f"Your {plan_name} subscription has ended. Renew to keep premium access active.",
                NotificationType.BILLING,
                dedupe_key=f"subscription_expired:{subscription.id}:{period_end.date().isoformat()}",
                data={
                    "event": "subscription_expired",
                    "subscription_id": subscription.id,
                    "plan_id": subscription.plan_id,
                    "period_end": period_end.isoformat(),
                },
                send_push=True,
            )

    async def ensure_usage_notifications(self, user: User) -> None:
        plan = await Plan.get(user.current_plan_id) if user.current_plan_id else None
        is_free = plan is None or plan.slug == "free"
        if not is_free:
            return

        limit = plan.generation_limit if plan else 5
        remaining = max(limit - user.monthly_generation_count, 0)
        if remaining not in {2, 1, 0}:
            return

        last_reset = ensure_utc(user.last_generation_reset_at) if user.last_generation_reset_at else utc_now()
        window_start = (last_reset - timedelta(days=last_reset.weekday())).date().isoformat()
        await self.create_notification_once(
            user,
            "Prompt quota update",
            (
                "You have reached your weekly prompt limit."
                if remaining == 0
                else f"You have {remaining} prompt generation{'s' if remaining != 1 else ''} left this week."
            ),
            NotificationType.USAGE,
            dedupe_key=f"usage_remaining:{user.id}:{window_start}:{remaining}",
            data={"event": "usage_remaining", "remaining": remaining, "window_start": window_start},
            send_push=remaining <= 1,
        )
