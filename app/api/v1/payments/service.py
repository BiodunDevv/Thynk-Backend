from uuid import uuid4

from app.api.v1.payments.schemas import InitializePaymentRequest, PaymentResponse
from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.payment import Payment, PaymentWebhookEvent
from app.models.plan import Plan
from app.models.user import User
from app.services.payments.payment_service import PaymentService
from app.services.payments.pricing import get_provider_amount_and_currency

payment_service = PaymentService()


async def initialize_payment(user: User, payload: InitializePaymentRequest) -> dict:
    plan = await Plan.get(payload.plan_id)
    if not plan or not plan.is_active:
        raise AppException(400, "Invalid or inactive plan.", ErrorCodes.PLAN_NOT_FOUND)

    charge_amount, charge_currency = get_provider_amount_and_currency(
        plan,
        payload.provider,
    )
    reference = f"pay_{uuid4().hex[:16]}"
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        provider=payload.provider,
        provider_reference=reference,
        amount=charge_amount,
        currency=charge_currency,
        metadata={
            "callback_url": payload.callback_url or get_settings().default_payment_callback_url,
            "plan_currency": plan.currency,
            "plan_amount": plan.price,
        },
    )
    await payment.insert()
    provider = payment_service.get_provider(payload.provider)
    provider_result = await provider.initialize_payment(
        {
            "email": user.email,
            "amount": int(charge_amount * 100),
            "currency": charge_currency,
            "reference": reference,
            "callback_url": payload.callback_url or get_settings().default_payment_callback_url,
        }
    )
    return {"payment": PaymentResponse.model_validate(payment.model_dump()), "authorization": provider_result}


async def verify_payment(reference: str) -> dict:
    payment = await Payment.find_one(Payment.provider_reference == reference)
    if not payment:
        raise AppException(404, "Payment not found.", ErrorCodes.PAYMENT_NOT_FOUND)
    provider = payment_service.get_provider(payment.provider)
    result = await provider.verify_payment(reference)
    payment.status = "success" if result.get("status") == "success" else payment.status
    await payment.save()
    return {"payment": PaymentResponse.model_validate(payment.model_dump()), "provider_data": result}


async def store_webhook(
    provider_name: str,
    payload: dict,
    signature: str | None = None,
    raw_body: bytes | None = None,
) -> dict:
    provider = payment_service.get_provider(provider_name)
    result = await provider.handle_webhook(payload, signature=signature, raw_body=raw_body)

    event_id = payload.get("id") or payload.get("event") or uuid4().hex
    exists = await PaymentWebhookEvent.find_one(PaymentWebhookEvent.provider == provider_name, PaymentWebhookEvent.event_id == event_id)
    if exists:
        return {"processed": True, "duplicate": True}
    event = PaymentWebhookEvent(provider=provider_name, event_id=event_id, payload=payload)
    await event.insert()
    return {"processed": True, "duplicate": False, "provider_result": result}


async def get_payment_provider_config() -> dict:
    settings = get_settings()
    return {
        "api_base_url": settings.api_base_url,
        "default_callback_url": settings.default_payment_callback_url,
        "providers": {
            "paystack": {
                "name": "Paystack",
                "webhook_url": settings.paystack_webhook_url,
                "callback_url": settings.default_payment_callback_url,
                "signature_header": "x-paystack-signature",
                "signature_source": "PAYSTACK_SECRET_KEY",
                "webhook_secret_required": False,
                "instructions": "Use your Thynk backend webhook URL in the Paystack dashboard. Paystack signs webhooks with your secret key, so no separate webhook secret is required.",
            },
            "stripe": {
                "name": "Stripe",
                "webhook_url": settings.stripe_webhook_url,
                "callback_url": settings.default_payment_callback_url,
                "signature_header": "stripe-signature",
                "signature_source": "STRIPE_WEBHOOK_SECRET",
                "webhook_secret_required": True,
                "instructions": "Use the Stripe webhook endpoint secret generated in your Stripe dashboard.",
            },
        },
    }


async def my_payments(user: User) -> list[PaymentResponse]:
    payments = await Payment.find(Payment.user_id == user.id).sort("-created_at").to_list()
    return [PaymentResponse.model_validate(item.model_dump()) for item in payments]
