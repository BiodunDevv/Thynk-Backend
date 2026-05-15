from fastapi import APIRouter, Depends, status

from app.api.v1.plans.schemas import PlanCreateRequest, PlanResponse, PlanUpdateRequest
from app.core.exceptions import AppException
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.plan import Plan
from app.models.user import User
from app.services.payments.pricing import get_plan_provider_prices

router = APIRouter(prefix="/plans", tags=["Plans"])
admin_router = APIRouter(prefix="/admin/plans", tags=["Admin Plans"])


def _serialize(item: Plan) -> PlanResponse:
    return PlanResponse.model_validate(
        {**item.model_dump(), "provider_prices": get_plan_provider_prices(item)}
    )


@router.get("", response_model=SuccessResponse[list[PlanResponse]], summary="List public plans")
async def list_plans():
    plans = await Plan.find(Plan.is_active == True).sort("price").to_list()  # noqa: E712
    return SuccessResponse(message="Plans fetched successfully.", data=[_serialize(p) for p in plans])


# ── Admin endpoints ────────────────────────────────────────────────

@admin_router.get("", response_model=SuccessResponse[list[PlanResponse]], summary="List all plans (admin)")
async def admin_list_plans(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    plans = await Plan.find().sort("price").to_list()
    return SuccessResponse(message="Plans fetched successfully.", data=[_serialize(p) for p in plans])


@admin_router.post("", response_model=SuccessResponse[PlanResponse], status_code=status.HTTP_201_CREATED, summary="Create plan")
async def admin_create_plan(payload: PlanCreateRequest, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    existing = await Plan.find_one(Plan.slug == payload.slug)
    if existing:
        raise AppException(409, "A plan with this slug already exists.", "PLAN_SLUG_CONFLICT")
    plan = Plan(**payload.model_dump())
    await plan.insert()
    return SuccessResponse(message="Plan created successfully.", data=_serialize(plan))


@admin_router.patch("/{plan_id}", response_model=SuccessResponse[PlanResponse], summary="Update plan")
async def admin_update_plan(plan_id: str, payload: PlanUpdateRequest, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    plan = await Plan.get(plan_id)
    if not plan:
        raise AppException(404, "Plan not found.", "NOT_FOUND")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(plan, key, value)
    await plan.save()
    return SuccessResponse(message="Plan updated successfully.", data=_serialize(plan))


@admin_router.patch("/{plan_id}/toggle", response_model=SuccessResponse[PlanResponse], summary="Toggle plan active status")
async def admin_toggle_plan(plan_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    plan = await Plan.get(plan_id)
    if not plan:
        raise AppException(404, "Plan not found.", "NOT_FOUND")
    plan.is_active = not plan.is_active
    await plan.save()
    return SuccessResponse(message=f"Plan {'activated' if plan.is_active else 'deactivated'}.", data=_serialize(plan))


@admin_router.delete("/{plan_id}", response_model=SuccessResponse[dict], summary="Delete plan")
async def admin_delete_plan(plan_id: str, _: User = Depends(require_role(role="SUPER_ADMIN"))):
    plan = await Plan.get(plan_id)
    if not plan:
        raise AppException(404, "Plan not found.", "NOT_FOUND")
    await plan.delete()
    return SuccessResponse(message="Plan deleted successfully.", data={"id": plan_id})
