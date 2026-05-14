from uuid import uuid4

from app.api.v1.payments.schemas import InitializePaymentRequest, PaymentResponse
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.payment import Payment, PaymentWebhookEvent
from app.models.plan import Plan
from app.models.user import User
from app.services.payments.payment_service import PaymentService

payment_service = PaymentService()


async def initialize_payment(user: User, payload: InitializePaymentRequest) -> dict:
    plan = await Plan.get(payload.plan_id)
    if not plan or not plan.is_active:
        raise AppException(400, "Invalid or inactive plan.", ErrorCodes.PLAN_NOT_FOUND)
    reference = f"pay_{uuid4().hex[:16]}"
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        provider=payload.provider,
        provider_reference=reference,
        amount=plan.price,
        currency=plan.currency,
        metadata={"callback_url": payload.callback_url},
    )
    await payment.insert()
    provider = payment_service.get_provider(payload.provider)
    provider_result = await provider.initialize_payment({"email": user.email, "amount": int(plan.price * 100), "reference": reference, "callback_url": payload.callback_url})
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


async def store_webhook(provider_name: str, payload: dict) -> dict:
    event_id = payload.get("id") or payload.get("event") or uuid4().hex
    exists = await PaymentWebhookEvent.find_one(PaymentWebhookEvent.provider == provider_name, PaymentWebhookEvent.event_id == event_id)
    if exists:
        return {"processed": True, "duplicate": True}
    event = PaymentWebhookEvent(provider=provider_name, event_id=event_id, payload=payload)
    await event.insert()
    provider = payment_service.get_provider(provider_name)
    result = await provider.handle_webhook(payload)
    return {"processed": True, "duplicate": False, "provider_result": result}


async def my_payments(user: User) -> list[PaymentResponse]:
    payments = await Payment.find(Payment.user_id == user.id).sort("-created_at").to_list()
    return [PaymentResponse.model_validate(item.model_dump()) for item in payments]
