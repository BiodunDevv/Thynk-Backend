from typing import Any

from pydantic import Field

from app.models.base import TimestampedDocument


class AppSetting(TimestampedDocument):
    key: str
    value: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "app_settings"
