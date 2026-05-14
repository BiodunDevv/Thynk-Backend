from app.models.base import TimestampedDocument


class TemplateConversion(TimestampedDocument):
    source_chat_id: str
    source_prompt_id: str | None = None
    source_user_id: str
    created_by_admin_id: str
    template_id: str | None = None
    original_content_snapshot: str
    sanitized_content: str
    conversion_status: str = "draft"
    admin_notes: str | None = None

    class Settings:
        name = "template_conversions"
