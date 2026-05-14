from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    SUPER_ADMIN = "SUPER_ADMIN"


class OtpPurpose(str, Enum):
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"


class SubscriptionStatus(str, Enum):
    FREE = "free"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class BillingInterval(str, Enum):
    FREE = "free"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class PromptCategory(str, Enum):
    DESIGN = "design"
    DEVELOPMENT = "development"
    STUDENT = "student"
    CONTENT = "content"
    MARKETING = "marketing"
    WRITING = "writing"
    BUSINESS = "business"


class PromptTone(str, Enum):
    PROFESSIONAL = "professional"
    SIMPLE = "simple"
    CREATIVE = "creative"
    ACADEMIC = "academic"
    PERSUASIVE = "persuasive"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    DIRECT = "direct"


class PromptPlatform(str, Enum):
    CHATGPT = "ChatGPT"
    CLAUDE = "Claude"
    GEMINI = "Gemini"
    MIDJOURNEY = "Midjourney"
    RUNWAY = "Runway"
    GENERAL_AI = "General AI"


class PromptComplexity(str, Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"
    EXPERT = "expert"
    STEP_BY_STEP = "step-by-step"


class PromptOutputFormat(str, Enum):
    PROMPT_ONLY = "prompt_only"
    PROMPT_WITH_CONTEXT = "prompt_with_context"
    PROMPT_WITH_EXAMPLES = "prompt_with_examples"
    PROMPT_WITH_INSTRUCTIONS = "prompt_with_instructions"


class CouponDiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    SYSTEM = "system"
    SUPPORT = "support"
    BILLING = "billing"
    ACCOUNT = "account"
    USAGE = "usage"


class RequestChatStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RequestChatSource(str, Enum):
    PROMPT_GENERATOR = "prompt_generator"
    TEMPLATE = "template"
    ASSISTANT_CHAT = "assistant_chat"


class SupportTicketCategory(str, Enum):
    ACCOUNT = "account"
    BILLING = "billing"
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"
    AI_GENERATION = "ai_generation"
    COUPON = "coupon"
    BUG = "bug"
    FEEDBACK = "feedback"
    ABUSE = "abuse"
    OTHER = "other"


class SupportPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicketStatus(str, Enum):
    OPEN = "open"
    PENDING_ADMIN = "pending_admin"
    PENDING_USER = "pending_user"
    RESOLVED = "resolved"
    CLOSED = "closed"
