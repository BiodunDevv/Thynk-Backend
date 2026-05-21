from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import get_settings


class WebPushService:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.web_push_vapid_public_key
            and self.settings.web_push_vapid_private_key
            and self.settings.web_push_vapid_subject
        )

    async def send(
        self,
        subscriptions: list[dict[str, Any]],
        title: str,
        body: str,
        data: dict | None = None,
    ) -> dict[str, int]:
        if not subscriptions or not self.is_configured:
            return {"sent": 0, "failed": 0}

        sent = 0
        failed = 0
        for subscription in subscriptions:
            try:
                await asyncio.to_thread(
                    self._send_one,
                    subscription,
                    title,
                    body,
                    data or {},
                )
                sent += 1
            except Exception:
                failed += 1

        return {"sent": sent, "failed": failed}

    def _send_one(
        self,
        subscription: dict[str, Any],
        title: str,
        body: str,
        data: dict,
    ) -> None:
        from pywebpush import webpush

        webpush(
            subscription_info=subscription,
            data=self._build_payload(title, body, data),
            vapid_private_key=self.settings.web_push_vapid_private_key,
            vapid_claims={"sub": self.settings.web_push_vapid_subject},
        )

    @staticmethod
    def _build_payload(title: str, body: str, data: dict) -> str:
        import json

        return json.dumps({"title": title, "body": body, "data": data})
