from typing import Any

from pydantic import Field

from app.models.base import TimestampedDocument


class AuditLog(TimestampedDocument):
    actor_id: str | None = None
    actor_role: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None

    class Settings:
        name = "audit_logs"
