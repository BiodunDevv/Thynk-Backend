from app.api.v1.payments.providers.base import PaymentProviderBase
from app.api.v1.payments.providers.paystack import PaystackProvider
from app.api.v1.payments.providers.stripe import StripeProvider


class PaymentService:
    def get_provider(self, provider_name: str) -> PaymentProviderBase:
        if provider_name == "stripe":
            return StripeProvider()
        return PaystackProvider()
