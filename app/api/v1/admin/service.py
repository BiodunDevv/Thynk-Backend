from collections import Counter
from datetime import timedelta

from app.api.v1.admin.schemas import (
    AIUsageAnalyticsPoint,
    AdminOverviewResponse,
    AnalyticsPoint,
    RankedAnalyticsItem,
    RevenueAnalyticsPoint,
    SystemAnalyticsResponse,
)
from app.core.constants import PaymentStatus, SubscriptionStatus
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.prompt import Prompt
from app.models.request_chat import RequestChat
from app.models.subscription import Subscription
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.utils.datetime import ensure_utc, utc_now


async def get_dashboard_overview() -> AdminOverviewResponse:
    total_users = await User.find_all().count()
    active_users = await User.find(User.is_active == True).count()
    verified_users = await User.find(User.is_verified == True).count()
    paying_users = await Subscription.find(Subscription.status == "active").count()
    total_prompts_generated = sum(user.prompt_generation_count for user in await User.find_all().to_list())
    open_support_tickets = await SupportTicket.find(SupportTicket.status == "open").count()
    reported_request_chats = await RequestChat.find(RequestChat.is_reported == True).count()
    return AdminOverviewResponse(
        total_users=total_users,
        active_users=active_users,
        verified_users=verified_users,
        paying_users=paying_users,
        total_prompts_generated=total_prompts_generated,
        open_support_tickets=open_support_tickets,
        reported_request_chats=reported_request_chats,
    )


def _day_key(value) -> str | None:
    if not value:
        return None
    try:
        return ensure_utc(value).date().isoformat()
    except Exception:
        return None


def _build_day_range(days: int) -> list[str]:
    today = utc_now().date()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(days - 1, -1, -1)]


def _zero_daily_counts(days: int) -> dict[str, int]:
    return {day: 0 for day in _build_day_range(days)}


async def get_system_analytics(days: int) -> SystemAnalyticsResponse:
    days = max(1, min(days, 365))
    day_range = _build_day_range(days)
    day_set = set(day_range)

    users = await User.find_all().to_list()
    subscriptions = await Subscription.find_all().to_list()
    plans = await Plan.find_all().to_list()
    payments = await Payment.find_all().to_list()
    prompts = await Prompt.find_all().to_list()
    request_chats = await RequestChat.find_all().to_list()

    plan_map = {plan.id: plan for plan in plans}

    total_tokens_all_time = 0
    total_ai_requests_all_time = 0
    total_failed_requests_all_time = 0

    ai_usage_daily: dict[str, dict[str, int]] = {
        day: {
            "total_requests": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "failed_requests": 0,
        }
        for day in day_range
    }

    category_counter: Counter[str] = Counter()
    platform_counter: Counter[str] = Counter()
    daily_new_users = _zero_daily_counts(days)
    daily_generations = _zero_daily_counts(days)
    revenue_by_day: dict[str, dict[str, float | str]] = {}

    for user in users:
        day = _day_key(user.created_at)
        if day and day in day_set:
            daily_new_users[day] += 1

    for prompt in prompts:
        category_counter[str(prompt.category)] += 1
        platform_counter[str(prompt.platform)] += 1
        day = _day_key(prompt.created_at)
        if day and day in day_set:
            daily_generations[day] += 1

    for chat in request_chats:
        category_counter[str(chat.category)] += 1
        for message in chat.messages:
            token_usage = int(message.token_usage or 0)
            is_assistant_turn = message.role == "assistant"
            if is_assistant_turn and token_usage > 0:
                total_ai_requests_all_time += 1
                total_tokens_all_time += token_usage
                day = _day_key(message.created_at)
                if day and day in day_set:
                    ai_usage_daily[day]["total_requests"] += 1
                    ai_usage_daily[day]["total_tokens"] += token_usage
                    ai_usage_daily[day]["completion_tokens"] += token_usage
                    daily_generations[day] += 1
            if is_assistant_turn and message.metadata.get("is_final"):
                platform_counter["request-chat"] += 1

    for payment in payments:
        status = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
        if status != PaymentStatus.SUCCESS.value:
            continue
        day = _day_key(payment.created_at)
        if not day or day not in day_set:
            continue
        bucket = revenue_by_day.setdefault(
            day,
            {"amount": 0.0, "currency": payment.currency or "USD"},
        )
        bucket["amount"] = float(bucket["amount"]) + float(payment.amount or 0)

    active_subscriptions = [subscription for subscription in subscriptions if subscription.status == SubscriptionStatus.ACTIVE]
    plan_distribution_counter: Counter[str] = Counter()
    for subscription in active_subscriptions:
        plan = plan_map.get(subscription.plan_id)
        plan_distribution_counter[plan.name if plan else subscription.plan_id or "Unknown"] += 1

    ai_usage = []
    for day in day_range:
        point = ai_usage_daily[day]
        avg_tokens = round(point["total_tokens"] / point["total_requests"]) if point["total_requests"] else 0
        ai_usage.append(
            AIUsageAnalyticsPoint(
                date=day,
                total_requests=point["total_requests"],
                total_tokens=point["total_tokens"],
                prompt_tokens=point["prompt_tokens"],
                completion_tokens=point["completion_tokens"],
                avg_tokens_per_request=avg_tokens,
                failed_requests=point["failed_requests"],
            )
        )

    success_rate_pct = 100.0
    if total_ai_requests_all_time > 0:
        success_rate_pct = round(
            ((total_ai_requests_all_time - total_failed_requests_all_time) / total_ai_requests_all_time) * 100,
            2,
        )

    return SystemAnalyticsResponse(
        ai_usage=ai_usage,
        total_tokens_all_time=total_tokens_all_time,
        total_ai_requests_all_time=total_ai_requests_all_time,
        avg_response_time_ms=0,
        success_rate_pct=success_rate_pct,
        top_categories=[
            RankedAnalyticsItem(category=name, count=count)
            for name, count in category_counter.most_common(8)
        ],
        top_platforms=[
            RankedAnalyticsItem(platform=name, count=count)
            for name, count in platform_counter.most_common(8)
        ],
        daily_new_users=[
            AnalyticsPoint(date=day, count=daily_new_users[day])
            for day in day_range
        ],
        daily_generations=[
            AnalyticsPoint(date=day, count=daily_generations[day])
            for day in day_range
        ],
        revenue_by_day=[
            RevenueAnalyticsPoint(
                date=day,
                amount=float(revenue_by_day.get(day, {}).get("amount", 0.0)),
                currency=str(revenue_by_day.get(day, {}).get("currency", "USD")),
            )
            for day in day_range
        ],
        plan_distribution=[
            RankedAnalyticsItem(plan=name, count=count)
            for name, count in plan_distribution_counter.most_common()
        ],
    )
