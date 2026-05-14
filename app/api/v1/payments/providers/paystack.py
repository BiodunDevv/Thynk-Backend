import httpx

from app.api.v1.payments.providers.base import PaymentProviderBase
from app.core.config import get_settings


class PaystackProvider(PaymentProviderBase):
    async def initialize_payment(self, payload: dict) -> dict:
        settings = get_settings()
        if not settings.paystack_secret_key:
            return {"authorization_url": "https://paystack.mock/authorize", "reference": payload["reference"]}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.paystack_base_url}/transaction/initialize",
                json=payload,
                headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            )
            response.raise_for_status()
            return response.json()["data"]

    async def verify_payment(self, reference: str) -> dict:
        settings = get_settings()
        if not settings.paystack_secret_key:
            return {"reference": reference, "status": "success"}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{settings.paystack_base_url}/transaction/verify/{reference}",
                headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
            )
            response.raise_for_status()
            return response.json()["data"]

    async def handle_webhook(self, payload: dict, signature: str | None = None) -> dict:
        return {"processed": True, "event_id": payload.get("event", "unknown")}
