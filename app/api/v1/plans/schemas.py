from pydantic import BaseModel, Field

from app.core.constants import BillingInterval


class ProviderPriceResponse(BaseModel):
    amount: float
    currency: str


class PlanResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    price: float
    currency: str
    billing_interval: BillingInterval
    generation_limit: int
    can_use_premium_templates: bool
    can_save_unlimited_prompts: bool
    priority_generation: bool
    is_active: bool
    provider_prices: dict[str, ProviderPriceResponse]


class PlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, pattern=r"^[a-z0-9-]+$")
    description: str = Field(..., min_length=1)
    price: float = Field(..., ge=0)
    currency: str = Field(default="NGN")
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    generation_limit: int = Field(..., ge=0)
    can_use_premium_templates: bool = False
    can_save_unlimited_prompts: bool = False
    priority_generation: bool = False
    is_active: bool = True


class PlanUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = None
    billing_interval: BillingInterval | None = None
    generation_limit: int | None = Field(default=None, ge=0)
    can_use_premium_templates: bool | None = None
    can_save_unlimited_prompts: bool | None = None
    priority_generation: bool | None = None
    is_active: bool | None = None
