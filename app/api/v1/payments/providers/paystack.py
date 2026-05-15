import hashlib
import hmac

import httpx

from app.api.v1.payments.providers.base import PaymentProviderBase
from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException


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

    async def handle_webhook(
        self,
        payload: dict,
        signature: str | None = None,
        raw_body: bytes | None = None,
    ) -> dict:
        settings = get_settings()
        if not settings.paystack_secret_key:
            raise AppException(
                503,
                "Paystack is not configured. Add your Paystack secret key before enabling webhooks.",
                ErrorCodes.PAYMENT_PROVIDER_ERROR,
            )
        if not signature or not raw_body:
            raise AppException(
                400,
                "Missing Paystack webhook signature.",
                ErrorCodes.PAYMENT_WEBHOOK_INVALID,
            )

        expected_signature = hmac.new(
            settings.paystack_secret_key.encode("utf-8"),
            raw_body,
            hashlib.sha512,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            raise AppException(
                400,
                "Invalid Paystack webhook signature.",
                ErrorCodes.PAYMENT_WEBHOOK_INVALID,
            )

        return {"processed": True, "event_id": payload.get("event", "unknown")}
