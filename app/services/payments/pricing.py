from app.models.plan import Plan

STRIPE_NGN_TO_USD_RATE = 1600


def get_provider_amount_and_currency(plan: Plan, provider_name: str) -> tuple[float, str]:
    if provider_name == "stripe":
        if plan.price <= 0:
            return 0, "USD"

        usd_amount = round(plan.price / STRIPE_NGN_TO_USD_RATE, 2)
        return max(usd_amount, 0.5), "USD"

    return plan.price, "NGN"


def get_plan_provider_prices(plan: Plan) -> dict[str, dict[str, float | str]]:
    paystack_amount, paystack_currency = get_provider_amount_and_currency(plan, "paystack")
    stripe_amount, stripe_currency = get_provider_amount_and_currency(plan, "stripe")

    return {
        "paystack": {
            "amount": paystack_amount,
            "currency": paystack_currency,
        },
        "stripe": {
            "amount": stripe_amount,
            "currency": stripe_currency,
        },
    }
