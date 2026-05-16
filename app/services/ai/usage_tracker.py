from datetime import datetime, timedelta, timezone

from app.core.constants import NotificationType
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.plan import Plan
from app.models.usage_credit import UsageCredit
from app.models.user import User
from app.services.notifications.notification_service import NotificationService

_FREE_RESET_DAYS = 7


class UsageTracker:
    def __init__(self) -> None:
        self.notification_service = NotificationService()

    async def _maybe_reset_free_count(self, user: User, is_free: bool) -> None:
        if not is_free:
            return
        now = datetime.now(timezone.utc)
        last = user.last_generation_reset_at
        previous_count = user.monthly_generation_count
        if last is None or (now - last.replace(tzinfo=timezone.utc)) >= timedelta(days=_FREE_RESET_DAYS):
            user.monthly_generation_count = 0
            user.last_generation_reset_at = now
            await user.save()
            if previous_count > 0:
                await self.notification_service.create_notification_once(
                    user,
                    "Weekly prompt quota refreshed",
                    "Your free weekly prompt generation quota has been refreshed.",
                    kind=NotificationType.USAGE,
                    dedupe_key=f"usage_reset:{user.id}:{now.date().isoformat()}",
                    data={"event": "usage_reset", "reset_date": now.isoformat()},
                    send_push=True,
                )

    async def sync_usage_window(self, user: User) -> User:
        plan = await Plan.get(user.current_plan_id) if user.current_plan_id else None
        is_free = plan is None or plan.slug == "free"
        await self._maybe_reset_free_count(user, is_free)
        return user

    async def ensure_generation_allowed(self, user: User) -> dict:
        plan = await Plan.get(user.current_plan_id) if user.current_plan_id else None
        limit = plan.generation_limit if plan else 5
        is_free = plan is None or plan.slug == "free"
        await self._maybe_reset_free_count(user, is_free)
        used = user.monthly_generation_count
        if limit >= 0 and used >= limit:
            credits = await UsageCredit.find(UsageCredit.user_id == user.id, UsageCredit.remaining > 0).to_list()
            total_remaining_credits = sum(item.remaining for item in credits)
            if total_remaining_credits <= 0:
                raise AppException(
                    403,
                    "You have reached your free prompt generation limit. Upgrade your plan to continue.",
                    ErrorCodes.PROMPT_LIMIT_REACHED,
                    details={"current_plan": plan.name if plan else "Free", "remaining_generations": 0, "upgrade_required": True},
                )
            first = credits[0]
            first.remaining -= 1
            await first.save()
            return {"remaining_generations": 0, "credits_used": 1}
        user.monthly_generation_count += 1
        user.prompt_generation_count += 1
        user.last_generation_reset_at = datetime.now(timezone.utc)
        await user.save()
        remaining = max(limit - user.monthly_generation_count, 0) if limit >= 0 else -1
        if is_free:
            await self.notification_service.ensure_usage_notifications(user)
        return {"remaining_generations": remaining, "credits_used": 0}
