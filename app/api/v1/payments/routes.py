from fastapi import APIRouter, Depends, Request

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.payments.schemas import InitializePaymentRequest, PaymentResponse
from app.api.v1.payments.service import initialize_payment, my_payments, store_webhook, verify_payment
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])
admin_router = APIRouter(prefix="/admin/payments", tags=["Admin Payments"])


@router.post("/initialize", response_model=SuccessResponse[dict], summary="Initialize payment", description="Initializes a payment for a selected plan.")
async def start_payment(payload: InitializePaymentRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payment initialized successfully.", data=await initialize_payment(user, payload))


@router.get("/verify/{reference}", response_model=SuccessResponse[dict], summary="Verify payment", description="Verifies a payment reference with the configured provider.")
async def confirm_payment(reference: str, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payment verified successfully.", data=await verify_payment(reference))


@router.post("/webhook/paystack", response_model=SuccessResponse[dict], summary="Paystack webhook", description="Processes Paystack webhook events idempotently. No authentication required.")
async def paystack_webhook(request: Request):
    payload = await request.json()
    return SuccessResponse(message="Webhook processed successfully.", data=await store_webhook("paystack", payload))


@router.post("/webhook/stripe", response_model=SuccessResponse[dict], summary="Stripe webhook", description="Processes Stripe webhook events idempotently. No authentication required.")
async def stripe_webhook(request: Request):
    payload = await request.json()
    return SuccessResponse(message="Webhook processed successfully.", data=await store_webhook("stripe", payload))


@router.get("/me", response_model=SuccessResponse[list[PaymentResponse]], summary="List my payments", description="Returns the logged-in user's payment history.")
async def list_my_payments(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Payments fetched successfully.", data=await my_payments(user))


@admin_router.get("", response_model=SuccessResponse[list[PaymentResponse]], summary="List all payments", description="Returns all payments. Requires Bearer token with SUPER_ADMIN role.")
async def list_all_payments(_=Depends(require_role(role="SUPER_ADMIN"))):
    from app.models.payment import Payment

    data = [PaymentResponse.model_validate(item.model_dump()) for item in await Payment.find_all().sort("-created_at").to_list()]
    return SuccessResponse(message="Payments fetched successfully.", data=data)
