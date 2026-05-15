from fastapi import APIRouter

from app.api.v1.admin.request_chats.routes import router as admin_request_chat_router
from app.api.v1.admin.routes import router as admin_router
from app.api.v1.admin.support.routes import router as admin_support_router
from app.api.v1.admin.users import router as admin_users_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.coupons.routes import admin_router as admin_coupon_router
from app.api.v1.coupons.routes import router as coupon_router
from app.api.v1.legal.routes import router as legal_router
from app.api.v1.notifications.routes import router as notification_router
from app.api.v1.payments.routes import admin_router as admin_payment_router
from app.api.v1.payments.routes import router as payment_router
from app.api.v1.plans.routes import admin_router as admin_plan_router
from app.api.v1.plans.routes import router as plan_router
from app.api.v1.prompts.routes import router as prompt_router
from app.api.v1.request_chats.routes import router as request_chat_router
from app.api.v1.subscriptions.routes import router as subscription_router
from app.api.v1.support.routes import router as support_router
from app.api.v1.templates.routes import admin_router as admin_template_router
from app.api.v1.templates.routes import router as template_router
from app.api.v1.users.routes import router as user_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(plan_router)
api_router.include_router(user_router)
api_router.include_router(prompt_router)
api_router.include_router(request_chat_router)
api_router.include_router(template_router)
api_router.include_router(subscription_router)
api_router.include_router(payment_router)
api_router.include_router(coupon_router)
api_router.include_router(notification_router)
api_router.include_router(support_router)
api_router.include_router(legal_router)
api_router.include_router(admin_router)
api_router.include_router(admin_request_chat_router)
api_router.include_router(admin_support_router)
api_router.include_router(admin_payment_router)
api_router.include_router(admin_coupon_router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_plan_router)
