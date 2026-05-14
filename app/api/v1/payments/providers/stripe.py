from app.api.v1.payments.providers.base import PaymentProviderBase


class StripeProvider(PaymentProviderBase):
    async def initialize_payment(self, payload: dict) -> dict:
        return {"message": "Stripe provider scaffolded for future implementation.", "payload": payload}

    async def verify_payment(self, reference: str) -> dict:
        return {"message": "Stripe provider scaffolded for future implementation.", "reference": reference}

    async def handle_webhook(self, payload: dict, signature: str | None = None) -> dict:
        return {"processed": False, "provider": "stripe", "payload": payload}
