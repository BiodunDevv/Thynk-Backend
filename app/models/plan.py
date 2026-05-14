from pydantic import Field

from app.core.constants import BillingInterval
from app.models.base import TimestampedDocument


class Plan(TimestampedDocument):
    name: str
    slug: str
    description: str
    price: float
    currency: str = "USD"
    billing_interval: BillingInterval
    generation_limit: int
    can_use_premium_templates: bool = False
    can_save_unlimited_prompts: bool = False
    priority_generation: bool = False
    is_active: bool = True

    class Settings:
        name = "plans"
