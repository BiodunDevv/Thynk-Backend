import httpx

from app.core.config import get_settings


class ExpoClient:
    async def send(self, tokens: list[str], title: str, body: str, data: dict | None = None) -> dict:
        if not tokens:
            return {"sent": 0}
        settings = get_settings()
        payload = [{"to": token, "title": title, "body": body, "data": data or {}} for token in tokens]
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(settings.expo_push_api_url, json=payload)
            response.raise_for_status()
            return response.json()
