from abc import ABC, abstractmethod


class PaymentProviderBase(ABC):
    @abstractmethod
    async def initialize_payment(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def verify_payment(self, reference: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def handle_webhook(self, payload: dict, signature: str | None = None) -> dict:
        raise NotImplementedError

    async def create_customer(self, payload: dict) -> dict:
        return {"supported": False}

    async def cancel_subscription(self, subscription_id: str) -> dict:
        return {"supported": False, "subscription_id": subscription_id}
