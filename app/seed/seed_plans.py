from app.core.constants import BillingInterval
from app.models.plan import Plan


DEFAULT_PLANS = [
    {
        "name": "Free",
        "slug": "free",
        "description": "Starter access for light prompt generation.",
        "price": 0,
        "currency": "NGN",
        "billing_interval": BillingInterval.FREE,
        "generation_limit": 5,
        "can_use_premium_templates": False,
        "can_save_unlimited_prompts": False,
        "priority_generation": False,
    },
    {
        "name": "Pro Monthly",
        "slug": "pro-monthly",
        "description": "Monthly premium access for Thynk power users.",
        "price": 2500,
        "currency": "NGN",
        "billing_interval": BillingInterval.MONTHLY,
        "generation_limit": 2500,
        "can_use_premium_templates": True,
        "can_save_unlimited_prompts": True,
        "priority_generation": True,
    },
    {
        "name": "Pro Yearly",
        "slug": "pro-yearly",
        "description": "Discounted yearly premium access.",
        "price": 25000,
        "currency": "NGN",
        "billing_interval": BillingInterval.YEARLY,
        "generation_limit": 30000,
        "can_use_premium_templates": True,
        "can_save_unlimited_prompts": True,
        "priority_generation": True,
    },
]


async def seed_plans() -> None:
    for item in DEFAULT_PLANS:
        exists = await Plan.find_one(Plan.slug == item["slug"])
        if not exists:
            await Plan(**item).insert()
            continue

        for key, value in item.items():
            setattr(exists, key, value)
        await exists.save()
