import httpx

from app.core.config import get_settings


class BrevoClient:
    async def send_email(self, payload: dict) -> dict:
        settings = get_settings()
        if not settings.brevo_api_key:
            return {"mocked": True, "payload": payload}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": settings.brevo_api_key, "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()
