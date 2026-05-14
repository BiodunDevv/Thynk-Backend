from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas import (
    AuthResponse,
    AuthUserResponse,
    ChangePasswordRequest,
    EmailOnlyRequest,
    LoginRequest,
    OTPRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.api.v1.auth.service import (
    change_password,
    login_user,
    logout,
    refresh_login,
    register_user,
    request_password_reset,
    resend_verification_code,
    reset_password,
    verify_email,
    verify_reset_code,
)
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=SuccessResponse[AuthUserResponse], status_code=status.HTTP_201_CREATED, summary="Register a new user", description="Creates a new user account and sends a 6-digit email verification code using Brevo.")
async def register(payload: RegisterRequest):
    data = await register_user(payload)
    return SuccessResponse(message="Account created successfully. Please verify your email.", data=data)


@router.post("/verify-email", response_model=SuccessResponse[AuthUserResponse], summary="Verify email address", description="Verifies a user account with a 6-digit email code.")
async def verify(payload: OTPRequest):
    return SuccessResponse(message="Email verified successfully.", data=await verify_email(payload))


@router.post("/resend-verification-code", response_model=SuccessResponse[dict], summary="Resend verification code", description="Sends a new 6-digit account verification code.")
async def resend(payload: EmailOnlyRequest):
    await resend_verification_code(payload)
    return SuccessResponse(message="Verification code sent successfully.", data={})


@router.post("/login", response_model=SuccessResponse[AuthResponse], summary="Login user", description="Authenticates a verified user and returns JWT tokens.")
async def login(payload: LoginRequest):
    return SuccessResponse(message="Login successful.", data=await login_user(payload))


@router.post("/refresh", response_model=SuccessResponse[AuthResponse], summary="Refresh access token", description="Rotates and refreshes the access token using a valid refresh token.")
async def refresh(payload: RefreshTokenRequest):
    return SuccessResponse(message="Token refreshed successfully.", data=await refresh_login(payload))


@router.post("/forgot-password", response_model=SuccessResponse[dict], summary="Request password reset code", description="Sends a 6-digit password reset code to the user's email.")
async def forgot_password(payload: EmailOnlyRequest):
    await request_password_reset(payload)
    return SuccessResponse(message="Password reset code sent successfully.", data={})


@router.post("/verify-reset-code", response_model=SuccessResponse[dict], summary="Verify password reset code", description="Checks that the submitted reset OTP is valid and not expired.")
async def verify_reset(payload: OTPRequest):
    await verify_reset_code(payload)
    return SuccessResponse(message="Reset code verified successfully.", data={})


@router.post("/reset-password", response_model=SuccessResponse[dict], summary="Reset password", description="Resets the user's password after OTP verification.")
async def reset(payload: ResetPasswordRequest):
    await reset_password(payload)
    return SuccessResponse(message="Password reset successfully.", data={})


@router.post("/change-password", response_model=SuccessResponse[dict], summary="Change password", description="Allows a logged-in user to change their password.")
async def change(payload: ChangePasswordRequest, user: User = Depends(get_current_user)):
    await change_password(user, payload)
    return SuccessResponse(message="Password changed successfully.", data={})


@router.post("/logout", response_model=SuccessResponse[dict], summary="Logout user", description="Invalidates the current refresh token session.",)
async def sign_out(user: User = Depends(get_current_user)):
    await logout(user)
    return SuccessResponse(message="Logged out successfully.", data={})
