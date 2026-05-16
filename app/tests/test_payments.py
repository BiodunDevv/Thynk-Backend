from unittest.mock import AsyncMock

import pytest

from datetime import datetime, timedelta, timezone

from app.api.v1.payments.service import (
    _build_payment_return_url,
    _build_plan_snapshot,
    _build_subscription_period_end,
    _extract_provider_status,
    verify_payment_for_user,
)
from app.core.exceptions import AppException
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.user import User


def make_payment(**overrides):
    base = {
        "id": "pay_1",
        "user_id": "user_1",
        "plan_id": "plan_1",
        "provider": "paystack",
        "provider_reference": "ref_123",
        "amount": 2500,
        "currency": "NGN",
        "status": "pending",
        "metadata": {},
        "coupon_id": None,
        "discount_amount": 0,
    }
    base.update(overrides)
    return Payment.model_construct(
        **base,
    )


def test_extract_provider_status_from_paystack_verify_payload():
    payload = {
        "reference": "ref_123",
        "status": "success",
        "gateway_response": "Successful",
        "customer": {"customer_code": "CUS_123"},
    }

    result = _extract_provider_status("paystack", payload, source="verify")

    assert result["reference"] == "ref_123"
    assert result["status"] == "success"
    assert result["message"] == "Successful"
    assert result["customer_code"] == "CUS_123"


def test_extract_provider_status_from_paystack_webhook_payload():
    payload = {
        "event": "charge.success",
        "data": {
            "reference": "ref_123",
            "status": "success",
            "gateway_response": "Approved",
        },
    }

    result = _extract_provider_status("paystack", payload, source="webhook")

    assert result["event"] == "charge.success"
    assert result["reference"] == "ref_123"
    assert result["status"] == "success"
    assert result["message"] == "Approved"


def test_build_plan_snapshot_prefers_payment_metadata():
    plan = Plan.model_construct(
        id="plan_1",
        name="Seed",
        slug="seed",
        description="desc",
        price=2500,
        currency="NGN",
        billing_interval="monthly",
        generation_limit=50,
        can_use_premium_templates=True,
        can_save_unlimited_prompts=True,
        priority_generation=False,
        is_active=True,
    )
    payment = make_payment(
        metadata={
            "plan_name": "Seed Legacy",
            "plan_slug": "seed-legacy",
            "billing_interval": "monthly",
            "plan_currency": "NGN",
            "plan_amount": 2500,
        }
    )

    snapshot = _build_plan_snapshot(plan, payment)

    assert snapshot is not None
    assert snapshot.name == "Seed Legacy"
    assert snapshot.slug == "seed-legacy"
    assert snapshot.provider_amount == 2500
    assert snapshot.provider_currency == "NGN"


def test_build_payment_return_url_preserves_existing_query_params():
    payment = make_payment(
        provider_reference="pay_ref_1",
        metadata={"callback_url": "http://localhost:3000/settings?tab=billing&payment=return"},
    )

    url = _build_payment_return_url(payment)

    assert "reference=pay_ref_1" in url
    assert "payment=return" in url
    assert "tab=billing" in url


def test_build_subscription_period_end_carries_forward_remaining_time():
    starts_at = datetime(2026, 5, 16, tzinfo=timezone.utc)
    carryover = timedelta(days=12)

    period_end = _build_subscription_period_end("yearly", starts_at=starts_at, carryover=carryover)

    assert period_end == starts_at + timedelta(days=377)


@pytest.mark.asyncio
async def test_verify_payment_for_user_rejects_foreign_payment(monkeypatch):
    payment = make_payment(user_id="owner_1")
    user = User.model_construct(id="user_2")

    find_payment = AsyncMock(return_value=payment)
    monkeypatch.setattr("app.api.v1.payments.service._find_payment_by_reference", find_payment)

    with pytest.raises(AppException) as exc:
        await verify_payment_for_user(user, "ref_123")

    assert exc.value.status_code == 403
