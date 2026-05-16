import json

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.payments.schemas import (
    InitializePaymentRequest,
    PaymentRecordResponse,
    PaymentResponse,
    PaymentVerificationResponse,
)
from app.api.v1.payments.service import (
    get_payment_provider_config,
    initialize_payment,
    my_payments,
    store_webhook,
    verify_payment_for_user,
)
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])
admin_router = APIRouter(prefix="/admin/payments", tags=["Admin Payments"])


@router.post("/initialize", response_model=SuccessResponse[dict], summary="Initialize payment", description="Initializes a payment for a selected plan.")
async def start_payment(payload: InitializePaymentRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payment initialized successfully.", data=await initialize_payment(user, payload))


@router.get("/verify/{reference}", response_model=SuccessResponse[PaymentVerificationResponse], response_model_exclude_none=True, summary="Verify payment", description="Verifies a payment reference with the configured provider and returns normalized billing state.")
async def confirm_payment(reference: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payment verified successfully.", data=await verify_payment_for_user(user, reference))


@router.get("/providers/config", response_model=SuccessResponse[dict], summary="Get payment provider configuration", description="Returns webhook, callback, and provider configuration details for billing setup screens.")
async def payment_provider_config(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payment provider configuration fetched successfully.", data=await get_payment_provider_config())


@router.post("/webhook/paystack", response_model=SuccessResponse[dict], summary="Paystack webhook", description="Processes Paystack webhook events idempotently. No authentication required.")
async def paystack_webhook(request: Request):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AppException(
            400,
            "Invalid webhook payload.",
            ErrorCodes.PAYMENT_WEBHOOK_INVALID,
        ) from exc
    signature = request.headers.get("x-paystack-signature")
    return SuccessResponse(
        message="Webhook processed successfully.",
        data=await store_webhook("paystack", payload, signature=signature, raw_body=raw_body),
    )


@router.post("/webhook/stripe", response_model=SuccessResponse[dict], summary="Stripe webhook", description="Processes Stripe webhook events idempotently. No authentication required.")
async def stripe_webhook(request: Request):
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AppException(
            400,
            "Invalid webhook payload.",
            ErrorCodes.PAYMENT_WEBHOOK_INVALID,
        ) from exc
    signature = request.headers.get("stripe-signature")
    return SuccessResponse(
        message="Webhook processed successfully.",
        data=await store_webhook("stripe", payload, signature=signature, raw_body=raw_body),
    )


@router.get("/me", response_model=SuccessResponse[list[PaymentRecordResponse]], response_model_exclude_none=True, summary="List my payments", description="Returns the logged-in user's normalized payment history.")
async def list_my_payments(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payments fetched successfully.", data=await my_payments(user))


@router.get("/history", response_model=SuccessResponse[list[PaymentRecordResponse]], response_model_exclude_none=True, summary="List payment history", description="Returns the logged-in user's normalized payment history using a cleaner frontend-friendly path.")
async def payment_history(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payments fetched successfully.", data=await my_payments(user))


@admin_router.get(
    "",
    response_model=SuccessResponse[list[PaymentRecordResponse]],
    response_model_exclude_none=True,
    summary="List all payments",
    description="Returns normalized payment records for the admin billing console, including resolved customer labels, plan snapshots, provider references, and payment timestamps.",
)
async def list_all_payments(_=Depends(require_role(role="SUPER_ADMIN"))):
    from app.models.payment import Payment
    from app.models.plan import Plan
    from app.models.user import User
    from app.api.v1.payments.service import _serialize_payment_record

    payments = await Payment.find_all().sort("-created_at").to_list()
    plan_ids = {payment.plan_id for payment in payments if payment.plan_id}
    user_ids = {payment.user_id for payment in payments if payment.user_id}
    plans = [await Plan.get(plan_id) for plan_id in plan_ids]
    users = [user for user in await User.find_all().to_list() if user.id in user_ids] if user_ids else []
    plan_map = {plan.id: plan for plan in plans if plan}
    user_map = {user.id: user for user in users}
    data = [_serialize_payment_record(item, plan_map.get(item.plan_id), user_map.get(item.user_id)) for item in payments]
    return SuccessResponse(message="Payments fetched successfully.", data=data)


@admin_router.get(
    "/{payment_id}",
    response_model=SuccessResponse[PaymentRecordResponse],
    response_model_exclude_none=True,
    summary="Get payment by ID",
    description="Returns a single normalized payment record for the admin portal. The response is optimized for billing review screens and should not require reading raw provider payloads.",
)
async def get_payment(payment_id: str, _=Depends(require_role(role="SUPER_ADMIN"))):
    from app.models.payment import Payment
    from app.models.plan import Plan
    from app.models.user import User
    from app.api.v1.payments.service import _serialize_payment_record
    from app.core.exceptions import AppException
    p = await Payment.get(payment_id)
    if not p:
        raise AppException(404, "Payment not found.", "NOT_FOUND")
    plan = await Plan.get(p.plan_id) if p.plan_id else None
    user = await User.get(p.user_id) if p.user_id else None
    return SuccessResponse(message="Payment fetched successfully.", data=_serialize_payment_record(p, plan, user))
