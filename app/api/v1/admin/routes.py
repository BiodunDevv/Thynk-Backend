from fastapi import APIRouter, Depends

from app.api.v1.admin.schemas import AdminOverviewResponse
from app.api.v1.admin.service import get_dashboard_overview
from app.api.v1.auth.schemas import AuthResponse, LoginRequest
from app.api.v1.auth.service import admin_login
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.post("/auth/login", response_model=SuccessResponse[AuthResponse], summary="Admin login", description="Authenticates a SUPER_ADMIN account. Non-admin accounts are rejected.")
async def admin_sign_in(payload: LoginRequest):
    return SuccessResponse(message="Admin login successful.", data=await admin_login(payload))


@router.get("/dashboard/overview", response_model=SuccessResponse[AdminOverviewResponse], summary="Get admin dashboard overview", description="Returns top-level metrics for the admin dashboard. Requires Bearer token with SUPER_ADMIN role.")
async def dashboard_overview(_: User = Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Dashboard metrics fetched successfully.", data=await get_dashboard_overview())
