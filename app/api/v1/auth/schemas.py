from pydantic import BaseModel, EmailStr, Field

from app.api.v1.common import AuthPayload, UserResponse


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name.", examples=["Clinton Kehinde"])
    email: EmailStr = Field(..., description="User's email address.", examples=["clinton@example.com"])
    password: str = Field(..., min_length=8, description="User password.", examples=["StrongPassword123!"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class OTPRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, examples=["123456"])


class EmailOnlyRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthUserResponse(BaseModel):
    user: UserResponse


class AuthResponse(BaseModel):
    tokens: dict
    user: UserResponse
    role: str
    plan: dict
    subscription_status: str
