import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie

from app.core.config import get_settings
from app.models.app_setting import AppSetting
from app.models.audit_log import AuditLog
from app.models.canned_reply import CannedReply
from app.models.collection import Collection
from app.models.coupon import Coupon, CouponRedemption
from app.models.notification import Notification
from app.models.otp import OTPCode
from app.models.payment import Payment, PaymentWebhookEvent
from app.models.plan import Plan
from app.models.prompt import Prompt
from app.models.prompt_template import PromptTemplate
from app.models.request_chat import RequestChat
from app.models.subscription import Subscription
from app.models.support_activity import SupportActivity
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.template_conversion import TemplateConversion
from app.models.usage_credit import UsageCredit
from app.models.user import User

client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    global client
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    await init_beanie(
        database=client[settings.mongodb_db_name],
        document_models=[
            User,
            OTPCode,
            Prompt,
            PromptTemplate,
            Collection,
            Subscription,
            Plan,
            Payment,
            PaymentWebhookEvent,
            Coupon,
            CouponRedemption,
            Notification,
            AuditLog,
            SupportTicket,
            SupportMessage,
            SupportActivity,
            AppSetting,
            RequestChat,
            TemplateConversion,
            CannedReply,
            UsageCredit,
        ],
    )


async def close_db() -> None:
    if client:
        client.close()
