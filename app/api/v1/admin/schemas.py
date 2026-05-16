from pydantic import BaseModel


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    paying_users: int
    total_prompts_generated: int
    open_support_tickets: int
    reported_request_chats: int


class AnalyticsPoint(BaseModel):
    date: str
    count: int


class AIUsageAnalyticsPoint(BaseModel):
    date: str
    total_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    avg_tokens_per_request: int
    failed_requests: int


class RevenueAnalyticsPoint(BaseModel):
    date: str
    amount: float
    currency: str


class RankedAnalyticsItem(BaseModel):
    category: str | None = None
    platform: str | None = None
    plan: str | None = None
    count: int


class SystemAnalyticsResponse(BaseModel):
    ai_usage: list[AIUsageAnalyticsPoint]
    total_tokens_all_time: int
    total_ai_requests_all_time: int
    avg_response_time_ms: int
    success_rate_pct: float
    top_categories: list[RankedAnalyticsItem]
    top_platforms: list[RankedAnalyticsItem]
    daily_new_users: list[AnalyticsPoint]
    daily_generations: list[AnalyticsPoint]
    revenue_by_day: list[RevenueAnalyticsPoint]
    plan_distribution: list[RankedAnalyticsItem]
