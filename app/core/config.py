from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Thynk", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    production_server_url: str = Field(default="https://api.thynk.app", alias="PRODUCTION_SERVER_URL")
    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="thynk", alias="MONGODB_DB_NAME")
    jwt_secret_key: str = Field(default="dev-jwt-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(
        default="dev-refresh-secret-change-me", alias="JWT_REFRESH_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    otp_expire_minutes: int = Field(default=10, alias="OTP_EXPIRE_MINUTES")
    otp_length: int = Field(default=6, alias="OTP_LENGTH")
    otp_max_attempts: int = Field(default=5, alias="OTP_MAX_ATTEMPTS")
    otp_request_limit: int = Field(default=5, alias="OTP_REQUEST_LIMIT")
    login_max_attempts: int = Field(default=5, alias="LOGIN_MAX_ATTEMPTS")
    login_lock_minutes: int = Field(default=15, alias="LOGIN_LOCK_MINUTES")
    brevo_api_key: str = Field(default="", alias="BREVO_API_KEY")
    brevo_sender_email: str = Field(default="no-reply@thynk.app", alias="BREVO_SENDER_EMAIL")
    brevo_sender_name: str = Field(default="Thynk", alias="BREVO_SENDER_NAME")
    ai_provider: str = Field(default="azure_openai", alias="AI_PROVIDER")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str = Field(
        default="", alias="AZURE_OPENAI_DEPLOYMENT_NAME"
    )
    azure_openai_model_name: str = Field(default="gpt-4.1-mini", alias="AZURE_OPENAI_MODEL_NAME")
    azure_openai_api_version: str = Field(
        default="2024-04-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_max_tokens: int = Field(default=1600, alias="AZURE_OPENAI_MAX_TOKENS")
    paystack_secret_key: str = Field(default="", alias="PAYSTACK_SECRET_KEY")
    paystack_public_key: str = Field(default="", alias="PAYSTACK_PUBLIC_KEY")
    paystack_base_url: str = Field(default="https://api.paystack.co", alias="PAYSTACK_BASE_URL")
    stripe_secret_key: str = Field(default="", alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")
    expo_push_api_url: str = Field(
        default="https://exp.host/--/api/v2/push/send", alias="EXPO_PUSH_API_URL"
    )
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    support_email: str = Field(default="support@thynk.app", alias="SUPPORT_EMAIL")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    super_admin_email: str = Field(default="", alias="SUPER_ADMIN_EMAIL")
    super_admin_password: str = Field(default="", alias="SUPER_ADMIN_PASSWORD")
    super_admin_name: str = Field(default="", alias="SUPER_ADMIN_NAME")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def api_base_url(self) -> str:
        return self.production_server_url.rstrip("/")

    @property
    def paystack_webhook_url(self) -> str:
        return f"{self.api_base_url}{self.api_v1_prefix}/payments/webhook/paystack"

    @property
    def stripe_webhook_url(self) -> str:
        return f"{self.api_base_url}{self.api_v1_prefix}/payments/webhook/stripe"

    @property
    def default_payment_callback_url(self) -> str:
        return f"{self.frontend_url.rstrip('/')}/settings?tab=billing&payment=return"

    @property
    def azure_openai_base_url(self) -> str:
        cleaned = self.azure_openai_endpoint.strip().rstrip("/")
        if not cleaned:
            return ""

        parsed = urlparse(cleaned)
        path = parsed.path.rstrip("/")
        if path.endswith("/responses"):
            path = path[: -len("/responses")]
        if path.endswith("/chat/completions"):
            path = path[: -len("/chat/completions")]
        if not path.endswith("/openai/v1"):
            path = f"{path}/openai/v1".rstrip("/")
        return parsed._replace(path=path).geturl().rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
