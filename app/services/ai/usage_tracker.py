from datetime import datetime, timezone

from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.plan import Plan
from app.models.usage_credit import UsageCredit
from app.models.user import User


class UsageTracker:
    async def ensure_generation_allowed(self, user: User) -> dict:
        plan = await Plan.get(user.current_plan_id) if user.current_plan_id else None
        limit = plan.generation_limit if plan else 5
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
        return {"remaining_generations": remaining, "credits_used": 0}
