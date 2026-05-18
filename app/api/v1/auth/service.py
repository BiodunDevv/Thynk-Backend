from datetime import timedelta

from app.api.v1.common import UserResponse
from app.api.v1.auth.schemas import (
    ChangePasswordRequest,
    EmailOnlyRequest,
    LoginRequest,
    OTPRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.core.config import get_settings
from app.core.constants import NotificationType, OtpPurpose, SubscriptionStatus, UserRole
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.core.security import decode_token, hash_password, hash_token, verify_password
from app.models.otp import OTPCode
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.api.v1.users.service import serialize_user_response
from app.services.auth.otp_service import OTPService
from app.services.auth.token_service import TokenService
from app.services.email.email_service import EmailService
from app.services.notifications.notification_service import NotificationService
from app.api.v1.payments.service import reconcile_user_billing_state
from app.utils.datetime import ensure_utc, utc_now
from app.utils.validators import normalize_email

user_repo = UserRepository()
otp_service = OTPService()
token_service = TokenService()
email_service = EmailService()
notification_service = NotificationService()


async def to_user_response(user: User) -> UserResponse:
    return await serialize_user_response(user)


async def register_user(payload: RegisterRequest) -> dict:
    email = normalize_email(payload.email)
    if await user_repo.get_by_email(email):
        raise AppException(409, "A user with this email already exists.", ErrorCodes.USER_ALREADY_EXISTS, field_errors=[{"field": "email", "message": "Email address is already registered."}])
    user = User(
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        subscription_status=SubscriptionStatus.FREE,
    )
    await user.insert()
    code = otp_service.generate_code()
    otp = OTPCode(email=email, code_hash=otp_service.hash_code(code), purpose=OtpPurpose.VERIFY_EMAIL, expires_at=utc_now() + timedelta(minutes=get_settings().otp_expire_minutes))
    await otp.insert()
    await email_service.send_verification_code(user.email, user.full_name, code)
    return {"user": await to_user_response(user)}


async def verify_email(payload: OTPRequest) -> dict:
    email = normalize_email(payload.email)
    code_hash = otp_service.hash_code(payload.code)
    # Find the most recent unused OTP that matches the submitted code
    otp = await OTPCode.find_one(
        OTPCode.email == email,
        OTPCode.purpose == OtpPurpose.VERIFY_EMAIL,
        OTPCode.is_used == False,
        OTPCode.code_hash == code_hash,
        sort=[("created_at", -1)],
    )
    if not otp:
        raise AppException(400, "Invalid verification code.", ErrorCodes.OTP_INVALID)
    if ensure_utc(otp.expires_at) < utc_now():
        raise AppException(400, "Verification code has expired.", ErrorCodes.OTP_EXPIRED)
    user = await user_repo.get_by_email(email)
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    user.is_verified = True
    await user.save()
    otp.is_used = True
    await otp.save()
    try:
        await email_service.send_welcome_email(user.email, user.full_name)
    except Exception:
        pass  # welcome email failure must never block verification
    await notification_service.create_notification_once(
        user,
        "Email verified",
        "Your account is now verified and ready to use.",
        NotificationType.ACCOUNT,
        dedupe_key=f"email_verified:{user.id}",
        data={"event": "email_verified"},
        send_push=True,
    )
    return {"user": await to_user_response(user)}


async def resend_verification_code(payload: EmailOnlyRequest) -> None:
    user = await user_repo.get_by_email(normalize_email(payload.email))
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    code = otp_service.generate_code()
    otp = OTPCode(email=user.email, code_hash=otp_service.hash_code(code), purpose=OtpPurpose.VERIFY_EMAIL, expires_at=utc_now() + timedelta(minutes=get_settings().otp_expire_minutes))
    await otp.insert()
    await email_service.send_verification_code(user.email, user.full_name, code)


async def login_user(payload: LoginRequest) -> dict:
    user = await user_repo.get_by_email(normalize_email(payload.email))
    settings = get_settings()
    if not user:
        raise AppException(
            401,
            "No account found with that email address.",
            ErrorCodes.AUTH_INVALID_CREDENTIALS,
            field_errors=[{"field": "email", "message": "No account found with this email address."}],
        )
    if not verify_password(payload.password, user.password_hash):
        raise AppException(
            401,
            "Incorrect password. Please try again.",
            ErrorCodes.AUTH_INVALID_CREDENTIALS,
            field_errors=[{"field": "password", "message": "The password you entered is incorrect."}],
        )
    if user.role == UserRole.SUPER_ADMIN:
        raise AppException(403, "Admin accounts must sign in through the admin portal.", ErrorCodes.AUTH_ACCOUNT_DISABLED)
    if not user.is_verified:
        # Auto-resend verification code so the user can verify immediately
        try:
            code = otp_service.generate_code()
            otp = OTPCode(email=user.email, code_hash=otp_service.hash_code(code), purpose=OtpPurpose.VERIFY_EMAIL, expires_at=utc_now() + timedelta(minutes=get_settings().otp_expire_minutes))
            await otp.insert()
            await email_service.send_verification_code(user.email, user.full_name, code)
        except Exception:
            pass
        raise AppException(403, "Please verify your email to continue. We just resent your verification code.", ErrorCodes.AUTH_EMAIL_NOT_VERIFIED)
    if not user.is_active:
        raise AppException(403, "Account is disabled.", ErrorCodes.AUTH_ACCOUNT_DISABLED)
    access_token = token_service.create_access_token(user.id)
    refresh_token, refresh_hash = token_service.create_refresh_token(user.id)
    user.refresh_token_hash = refresh_hash
    await user.save()
    return await _build_auth_payload(user, access_token, refresh_token)


async def admin_login(payload: LoginRequest) -> dict:
    user = await user_repo.get_by_email(normalize_email(payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppException(401, "Invalid email or password.", ErrorCodes.AUTH_INVALID_CREDENTIALS)
    if user.role != UserRole.SUPER_ADMIN:
        raise AppException(403, "Access denied. This portal is for administrators only.", ErrorCodes.AUTH_ACCOUNT_DISABLED)
    if not user.is_active:
        raise AppException(403, "Account is disabled.", ErrorCodes.AUTH_ACCOUNT_DISABLED)
    access_token = token_service.create_access_token(user.id)
    refresh_token, refresh_hash = token_service.create_refresh_token(user.id)
    user.refresh_token_hash = refresh_hash
    await user.save()
    return {
        "tokens": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"},
        "user": await to_user_response(user),
        "role": user.role.value,
        "plan": {"plan_id": user.current_plan_id},
        "subscription_status": user.subscription_status.value,
    }


async def _build_auth_payload(user: User, access_token: str, refresh_token: str) -> dict:
    """Build the full auth response with live plan + subscription data."""
    from app.models.plan import Plan

    user, subscription, _ = await reconcile_user_billing_state(user)

    # Resolve plan — prefer subscription's plan_id over user's current_plan_id
    plan_id = (subscription.plan_id if subscription else None) or user.current_plan_id
    plan = await Plan.get(plan_id) if plan_id else None

    plan_data: dict = {"plan_id": plan_id}
    if plan:
        plan_data = {
            "plan_id": plan.id,
            "name": plan.name,
            "slug": plan.slug,
            "price": plan.price,
            "currency": plan.currency,
            "billing_interval": plan.billing_interval,
            "generation_limit": plan.generation_limit,
            "can_use_premium_templates": plan.can_use_premium_templates,
            "can_save_unlimited_prompts": plan.can_save_unlimited_prompts,
            "priority_generation": plan.priority_generation,
        }

    subscription_data: dict = {}
    if subscription:
        subscription_data = {
            "id": str(subscription.id),
            "status": subscription.status.value,
            "provider": subscription.provider,
            "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    return {
        "tokens": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"},
        "user": await to_user_response(user),
        "role": user.role.value,
        "plan": plan_data,
        "subscription_status": user.subscription_status.value,
        "subscription": subscription_data,
    }


async def refresh_login(payload: RefreshTokenRequest) -> dict:
    token_payload = decode_token(payload.refresh_token, refresh=True)
    user = await User.get(token_payload["sub"])
    if not user or user.refresh_token_hash != hash_token(payload.refresh_token):
        raise AppException(401, "Invalid refresh token.", ErrorCodes.AUTH_REFRESH_TOKEN_INVALID)
    access_token = token_service.create_access_token(user.id)
    refresh_token, refresh_hash = token_service.create_refresh_token(user.id)
    user.refresh_token_hash = refresh_hash
    await user.save()
    return await _build_auth_payload(user, access_token, refresh_token)


async def request_password_reset(payload: EmailOnlyRequest) -> None:
    user = await user_repo.get_by_email(normalize_email(payload.email))
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    code = otp_service.generate_code()
    otp = OTPCode(email=user.email, code_hash=otp_service.hash_code(code), purpose=OtpPurpose.RESET_PASSWORD, expires_at=utc_now() + timedelta(minutes=get_settings().otp_expire_minutes))
    await otp.insert()
    await email_service.send_password_reset_code(user.email, user.full_name, code)


async def verify_reset_code(payload: OTPRequest) -> None:
    email = normalize_email(payload.email)
    code_hash = otp_service.hash_code(payload.code)
    otp = await OTPCode.find_one(
        OTPCode.email == email,
        OTPCode.purpose == OtpPurpose.RESET_PASSWORD,
        OTPCode.is_used == False,
        OTPCode.code_hash == code_hash,
        sort=[("created_at", -1)],
    )
    if not otp:
        raise AppException(400, "Invalid reset code.", ErrorCodes.OTP_INVALID)
    if ensure_utc(otp.expires_at) < utc_now():
        raise AppException(400, "Reset code has expired.", ErrorCodes.OTP_EXPIRED)


async def reset_password(payload: ResetPasswordRequest) -> None:
    await verify_reset_code(OTPRequest(email=payload.email, code=payload.code))
    user = await user_repo.get_by_email(normalize_email(payload.email))
    if not user:
        raise AppException(404, "User not found.", ErrorCodes.USER_NOT_FOUND)
    user.password_hash = hash_password(payload.new_password)
    await user.save()


async def change_password(user: User, payload: ChangePasswordRequest) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise AppException(400, "Current password is incorrect.", ErrorCodes.AUTH_INVALID_CREDENTIALS)
    user.password_hash = hash_password(payload.new_password)
    await user.save()


async def logout(user: User) -> None:
    user.refresh_token_hash = None
    await user.save()
