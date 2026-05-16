import logging
from uuid import uuid4
from urllib.parse import urlencode
from datetime import datetime

from app.api.v1.payments.schemas import (
    BillingStateResponse,
    InitializePaymentRequest,
    PaymentPlanSnapshotResponse,
    PaymentRecordResponse,
    PaymentResponse,
    PaymentVerificationResponse,
    ProviderStatusResponse,
)
from app.api.v1.subscriptions.schemas import SubscriptionResponse
from app.core.config import get_settings
from app.core.constants import NotificationType, PaymentStatus, SubscriptionStatus
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.payment import Payment, PaymentWebhookEvent
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.user import User
from app.services.email.email_service import EmailService
from app.services.notifications.notification_service import NotificationService
from app.services.payments.payment_service import PaymentService
from app.services.payments.pricing import get_provider_amount_and_currency
from app.utils.datetime import ensure_utc, utc_now

payment_service = PaymentService()
notification_service = NotificationService()
email_service = EmailService()
logger = logging.getLogger(__name__)


def _metadata_value(metadata: dict, key: str):
    value = metadata.get(key)
    return value if value not in ("", None, {}, []) else None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return ensure_utc(datetime.fromisoformat(value))
    except (TypeError, ValueError):
        return None


def _build_payment_return_url(payment: Payment) -> str:
    callback_url = (payment.metadata or {}).get("callback_url") or get_settings().default_payment_callback_url
    separator = "&" if "?" in callback_url else "?"
    return f"{callback_url}{separator}{urlencode({'reference': payment.provider_reference, 'payment': 'return'})}"


def _build_plan_snapshot(plan: Plan | None, payment: Payment) -> PaymentPlanSnapshotResponse | None:
    metadata = payment.metadata or {}
    if not plan and not metadata:
        return None

    return PaymentPlanSnapshotResponse(
        plan_id=payment.plan_id,
        name=_metadata_value(metadata, "plan_name") or (plan.name if plan else None),
        slug=_metadata_value(metadata, "plan_slug") or (plan.slug if plan else None),
        billing_interval=_metadata_value(metadata, "billing_interval") or (plan.billing_interval.value if plan else None),
        plan_currency=_metadata_value(metadata, "plan_currency") or (plan.currency if plan else None),
        plan_amount=_metadata_value(metadata, "plan_amount") or (plan.price if plan else None),
        provider_currency=payment.currency,
        provider_amount=payment.amount,
    )


def _serialize_payment_record(payment: Payment, plan: Plan | None = None, user: User | None = None) -> PaymentRecordResponse:
    plan_snapshot = _build_plan_snapshot(plan, payment)
    metadata = payment.metadata or {}
    return PaymentRecordResponse.model_validate(
        {
            **payment.model_dump(mode="json"),
            "plan_snapshot": plan_snapshot.model_dump() if plan_snapshot else None,
            "user_name": (user.full_name if user else None) or _metadata_value(metadata, "user_name_snapshot"),
            "user_email": (user.email if user else None) or _metadata_value(metadata, "user_email_snapshot"),
            "plan_name": plan_snapshot.name if plan_snapshot else None,
        }
    )


def _build_subscription_response(subscription: Subscription | None) -> SubscriptionResponse | None:
    if not subscription:
        return None
    return SubscriptionResponse.model_validate(subscription.model_dump(mode="json"))


def _build_billing_state(
    user: User | None,
    payment: Payment,
    subscription: Subscription | None,
    *,
    resolved_via: str,
) -> BillingStateResponse:
    return BillingStateResponse(
        current_plan_id=user.current_plan_id if user else None,
        subscription_id=subscription.id if subscription else (user.subscription_id if user else None),
        subscription_status=(subscription.status.value if subscription else (user.subscription_status.value if user else SubscriptionStatus.FREE.value)),
        payment_status=payment.status.value if hasattr(payment.status, "value") else str(payment.status),
        granted=bool(subscription and subscription.status == SubscriptionStatus.ACTIVE),
        resolved_via=resolved_via,
    )


def _extract_provider_status(provider_name: str, payload: dict, *, source: str) -> dict:
    if provider_name == "paystack":
        if source == "verify":
            return {
                "provider": provider_name,
                "reference": payload.get("reference"),
                "status": payload.get("status", "pending"),
                "event": None,
                "message": payload.get("gateway_response") or payload.get("message"),
                "source": source,
                "customer_code": (payload.get("customer") or {}).get("customer_code") or payload.get("customer_code"),
                "raw": payload,
            }

        event = payload.get("event")
        data = payload.get("data") or {}
        event_status_map = {
            "charge.success": "success",
            "charge.failed": "failed",
            "charge.dispute.create": "failed",
            "paymentrequest.pending": "pending",
            "paymentrequest.success": "success",
        }
        return {
            "provider": provider_name,
            "reference": data.get("reference"),
            "status": event_status_map.get(event, data.get("status", "pending")),
            "event": event,
            "message": data.get("gateway_response") or data.get("message"),
            "source": source,
            "customer_code": (data.get("customer") or {}).get("customer_code") or data.get("customer_code"),
            "raw": payload,
        }

    return {
        "provider": provider_name,
        "reference": payload.get("reference"),
        "status": payload.get("status", "pending"),
        "event": payload.get("event"),
        "message": payload.get("message"),
        "source": source,
        "customer_code": None,
        "raw": payload,
    }


async def _get_user_subscription(user_id: str) -> Subscription | None:
    return await Subscription.find_one(Subscription.user_id == user_id)


async def _find_payment_by_reference(reference: str) -> Payment | None:
    return await Payment.find_one({"provider_reference": reference})


async def reconcile_user_billing_state(user: User) -> tuple[User, Subscription | None, Plan | None]:
    subscription = None
    if user.subscription_id:
        subscription = await Subscription.get(user.subscription_id)

    if not subscription:
        subscription = await Subscription.find_one(Subscription.user_id == user.id)

    if not subscription:
        successful_payments = await Payment.find(
            Payment.user_id == user.id,
            Payment.status == PaymentStatus.SUCCESS,
        ).sort("-updated_at", "-created_at").limit(1).to_list()
        latest_successful_payment = successful_payments[0] if successful_payments else None
        if latest_successful_payment:
            _, subscription, _ = await _sync_subscription_success(
                latest_successful_payment,
                transition_source="reconcile",
                send_customer_email=False,
            )

    plan = None
    if subscription and subscription.plan_id:
        plan = await Plan.get(subscription.plan_id)
        needs_save = False
        if user.current_plan_id != subscription.plan_id:
            user.current_plan_id = subscription.plan_id
            needs_save = True
        if user.subscription_id != subscription.id:
            user.subscription_id = subscription.id
            needs_save = True
        if user.subscription_status != SubscriptionStatus.ACTIVE:
            user.subscription_status = SubscriptionStatus.ACTIVE
            needs_save = True
        if needs_save:
            await user.save()

    return user, subscription, plan


async def _sync_subscription_success(
    payment: Payment,
    *,
    transition_source: str,
    send_customer_email: bool = True,
) -> tuple[User | None, Subscription | None, Plan | None]:
    plan = await Plan.get(payment.plan_id)
    if not plan:
        raise AppException(404, "Plan not found for payment.", ErrorCodes.PLAN_NOT_FOUND)

    from datetime import timedelta

    completed_at = _parse_datetime((payment.metadata or {}).get("payment_completed_at")) or utc_now()
    now = completed_at
    if plan.billing_interval == "yearly":
        period_end = now + timedelta(days=365)
    elif plan.billing_interval == "monthly":
        period_end = now + timedelta(days=30)
    else:
        period_end = None

    subscription = await _get_user_subscription(payment.user_id)
    subscription_was_active = bool(subscription and subscription.status == SubscriptionStatus.ACTIVE)
    if subscription:
        should_reset_period = (
            subscription.plan_id != payment.plan_id
            or subscription.status != SubscriptionStatus.ACTIVE
            or not subscription.current_period_start
            or not subscription.current_period_end
            or (subscription.current_period_end and ensure_utc(subscription.current_period_end) <= now)
        )
        subscription.plan_id = payment.plan_id
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.provider = payment.provider
        subscription.provider_subscription_id = payment.provider_reference
        if should_reset_period:
            subscription.current_period_start = now
            subscription.current_period_end = period_end
        subscription.cancel_at_period_end = False
        await subscription.save()
    else:
        subscription = Subscription(
            user_id=payment.user_id,
            plan_id=payment.plan_id,
            status=SubscriptionStatus.ACTIVE,
            provider=payment.provider,
            provider_subscription_id=payment.provider_reference,
            current_period_start=now,
            current_period_end=period_end,
        )
        await subscription.insert()

    user = await User.get(payment.user_id)
    if user:
        user.current_plan_id = payment.plan_id
        user.subscription_status = SubscriptionStatus.ACTIVE
        user.subscription_id = subscription.id
        await user.save()

        payment.metadata = {
            **(payment.metadata or {}),
            "resolved_subscription_id": subscription.id,
            "payment_completed_at": completed_at.isoformat(),
            "last_transition_source": transition_source,
        }

        if not subscription_was_active:
            await notification_service.create_notification_once(
                user,
                "Subscription activated",
                f"Your payment was successful and {plan.name} is now active.",
                NotificationType.BILLING,
                dedupe_key=f"subscription_activated:{payment.provider_reference}",
                data={
                    "event": "subscription_activated",
                    "payment_id": payment.id,
                    "subscription_id": subscription.id,
                    "plan_id": plan.id,
                    "provider": payment.provider,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "resolved_via": transition_source,
                },
                send_push=True,
            )

        should_send_followup_email = (
            send_customer_email
            and
            transition_source == "webhook"
            and not (payment.metadata or {}).get("customer_return_confirmed_at")
            and not (payment.metadata or {}).get("payment_followup_email_sent_at")
        )
        if should_send_followup_email:
            try:
                await email_service.send_payment_completion(
                    email=user.email,
                    name=user.full_name,
                    plan=plan.name,
                    manage_url=_build_payment_return_url(payment),
                )
                payment.metadata["payment_followup_email_sent_at"] = utc_now().isoformat()
            except Exception:
                logger.exception("Failed to send payment completion email", extra={"payment_id": payment.id})

        await payment.save()

    return user, subscription, plan


async def _sync_payment_failure(
    payment: Payment,
    *,
    transition_source: str,
    notify_user_once: bool,
) -> tuple[User | None, Subscription | None, Plan | None]:
    user = await User.get(payment.user_id)
    subscription = await _get_user_subscription(payment.user_id)
    plan = await Plan.get(payment.plan_id)
    if user and notify_user_once:
        await notification_service.create_notification_once(
            user,
            "Payment not completed",
            "We couldn't complete your payment. Try again to continue with your selected plan.",
            NotificationType.BILLING,
            dedupe_key=f"payment_failed:{payment.provider_reference}",
            data={
                "event": "payment_failed",
                "payment_id": payment.id,
                "reference": payment.provider_reference,
                "provider": payment.provider,
                "plan_id": payment.plan_id,
                "resolved_via": transition_source,
            },
            send_push=True,
        )
        try:
            await email_service.send_payment_failed(user.email, user.full_name)
        except Exception:
            logger.exception("Failed to send payment failed email", extra={"payment_id": payment.id})
    return user, subscription, plan


async def _apply_payment_transition(
    payment: Payment,
    provider_payload: dict,
    *,
    source: str,
) -> tuple[PaymentVerificationResponse, dict]:
    provider_status = _extract_provider_status(payment.provider, provider_payload, source=source)
    status = provider_status["status"]
    reference = provider_status["reference"] or payment.provider_reference
    if reference != payment.provider_reference:
        raise AppException(400, "Provider reference mismatch.", ErrorCodes.PAYMENT_VERIFICATION_FAILED)

    payment.provider_customer_id = provider_status.get("customer_code") or payment.provider_customer_id
    payment.metadata = {
        **(payment.metadata or {}),
        "provider_last_status": status,
        "provider_last_event": provider_status.get("event"),
        "provider_message": provider_status.get("message"),
        "provider_synced_at": utc_now().isoformat(),
        "resolved_via": source,
        "last_transition_source": source,
    }

    previous_status = payment.status
    already_verified = payment.status == PaymentStatus.SUCCESS
    if status == "success":
        if not payment.metadata.get("payment_completed_at"):
            paid_at = (
                provider_payload.get("paid_at")
                or provider_payload.get("paidAt")
                or provider_payload.get("transaction_date")
                or provider_payload.get("created_at")
                or provider_payload.get("createdAt")
            )
            completed_at = _parse_datetime(paid_at) or utc_now()
            payment.metadata["payment_completed_at"] = completed_at.isoformat()
        if source == "verify":
            payment.metadata["customer_return_confirmed_at"] = utc_now().isoformat()
        payment.status = PaymentStatus.SUCCESS
        await payment.save()
        user, subscription, plan = await _sync_subscription_success(payment, transition_source=source)
    elif status in {"failed", "abandoned", "cancelled"}:
        payment.status = PaymentStatus.FAILED if status != "cancelled" else PaymentStatus.CANCELLED
        await payment.save()
        user, subscription, plan = await _sync_payment_failure(
            payment,
            transition_source=source,
            notify_user_once=previous_status not in {PaymentStatus.FAILED, PaymentStatus.CANCELLED},
        )
    else:
        await payment.save()
        user = await User.get(payment.user_id)
        if user:
            user, subscription, plan = await reconcile_user_billing_state(user)
        else:
            subscription = await _get_user_subscription(payment.user_id)
            plan = await Plan.get(payment.plan_id)

    payment_response = _serialize_payment_record(payment, plan)
    subscription_response = _build_subscription_response(subscription)
    billing_state = _build_billing_state(user, payment, subscription, resolved_via=source)
    result = PaymentVerificationResponse(
        payment=payment_response,
        plan_snapshot=payment_response.plan_snapshot,
        subscription=subscription_response,
        billing_state=billing_state,
        provider_status=ProviderStatusResponse.model_validate(provider_status),
        provider_debug=provider_payload or None,
        already_verified=already_verified,
    )
    logger.info(
        "payment_transition_applied",
        extra={
            "provider": payment.provider,
            "reference": payment.provider_reference,
            "payment_id": payment.id,
            "subscription_id": subscription.id if subscription else None,
            "transition_source": source,
            "status": status,
        },
    )
    return result, provider_status


async def initialize_payment(user: User, payload: InitializePaymentRequest) -> dict:
    plan = await Plan.get(payload.plan_id)
    if not plan or not plan.is_active:
        raise AppException(400, "Invalid or inactive plan.", ErrorCodes.PLAN_NOT_FOUND)

    charge_amount, charge_currency = get_provider_amount_and_currency(plan, payload.provider)
    reference = f"pay_{uuid4().hex[:16]}"
    callback_url = payload.callback_url or get_settings().default_payment_callback_url
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        provider=payload.provider,
        provider_reference=reference,
        amount=charge_amount,
        currency=charge_currency,
        metadata={
            "callback_url": callback_url,
            "plan_currency": plan.currency,
            "plan_amount": plan.price,
            "plan_name": plan.name,
            "plan_slug": plan.slug,
            "billing_interval": plan.billing_interval.value,
            "provider_amount": charge_amount,
            "provider_currency": charge_currency,
            "initialization_source": "checkout",
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
            "callback_url": callback_url,
        }
    )
    return {
        "payment": _serialize_payment_record(payment, plan),
        "authorization": provider_result,
    }


async def verify_payment(reference: str) -> PaymentVerificationResponse:
    payment = await _find_payment_by_reference(reference)
    if not payment:
        raise AppException(404, "Payment not found.", ErrorCodes.PAYMENT_NOT_FOUND)

    provider = payment_service.get_provider(payment.provider)
    result = await provider.verify_payment(reference)
    response, _ = await _apply_payment_transition(payment, result, source="verify")
    return response


async def verify_payment_for_user(user: User, reference: str) -> PaymentVerificationResponse:
    payment = await _find_payment_by_reference(reference)
    if not payment:
        raise AppException(404, "Payment not found.", ErrorCodes.PAYMENT_NOT_FOUND)
    if payment.user_id != user.id:
        raise AppException(403, "You cannot verify another user's payment.", ErrorCodes.AUTH_PERMISSION_DENIED)
    provider = payment_service.get_provider(payment.provider)
    result = await provider.verify_payment(reference)
    response, _ = await _apply_payment_transition(payment, result, source="verify")
    return response


async def store_webhook(
    provider_name: str,
    payload: dict,
    signature: str | None = None,
    raw_body: bytes | None = None,
) -> dict:
    provider = payment_service.get_provider(provider_name)
    validation_result = await provider.handle_webhook(payload, signature=signature, raw_body=raw_body)

    extracted = _extract_provider_status(provider_name, payload, source="webhook")
    event_id = payload.get("id") or payload.get("event") or uuid4().hex
    reference = extracted.get("reference")
    existing = await PaymentWebhookEvent.find_one(
        PaymentWebhookEvent.provider == provider_name,
        PaymentWebhookEvent.event_id == event_id,
    )
    if existing:
        existing.processing_status = "duplicate"
        existing.processing_message = "Webhook already processed."
        existing.processed_at = utc_now()
        await existing.save()
        return {"processed": True, "duplicate": True, "status": "duplicate"}

    webhook_event = PaymentWebhookEvent(
        provider=provider_name,
        event_id=event_id,
        provider_reference=reference,
        payload=payload,
        processing_status="accepted",
        transition_source="webhook",
    )
    await webhook_event.insert()

    if not reference:
        webhook_event.processing_status = "ignored"
        webhook_event.processing_message = "Webhook payload did not contain a provider reference."
        webhook_event.processed_at = utc_now()
        await webhook_event.save()
        return {"processed": True, "duplicate": False, "status": "ignored", "provider_result": validation_result}

    payment = await Payment.find_one(Payment.provider_reference == reference)
    if not payment:
        webhook_event.processing_status = "ignored"
        webhook_event.processing_message = "Payment reference not found."
        webhook_event.processed_at = utc_now()
        await webhook_event.save()
        return {"processed": True, "duplicate": False, "status": "ignored", "provider_result": validation_result}

    try:
        response, provider_status = await _apply_payment_transition(payment, payload, source="webhook")
        webhook_event.payment_id = payment.id
        webhook_event.processing_status = f"processed_{provider_status['status']}"
        webhook_event.processing_message = provider_status.get("message")
        webhook_event.processed_at = utc_now()
        await webhook_event.save()
        return {
            "processed": True,
            "duplicate": False,
            "status": webhook_event.processing_status,
            "payment_id": payment.id,
            "provider_reference": payment.provider_reference,
            "provider_result": validation_result,
            "billing_state": response.billing_state.model_dump(),
        }
    except Exception as exc:
        webhook_event.payment_id = payment.id
        webhook_event.processing_status = "processing_error"
        webhook_event.processing_message = str(exc)
        webhook_event.processed_at = utc_now()
        await webhook_event.save()
        raise


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


async def my_payments(user: User) -> list[PaymentRecordResponse]:
    user, _, _ = await reconcile_user_billing_state(user)
    payments = await Payment.find(Payment.user_id == user.id).sort("-created_at").to_list()
    plan_ids = {payment.plan_id for payment in payments if payment.plan_id}
    plans = [await Plan.get(plan_id) for plan_id in plan_ids]
    plan_map = {plan.id: plan for plan in plans if plan}
    return [_serialize_payment_record(item, plan_map.get(item.plan_id)) for item in payments]
