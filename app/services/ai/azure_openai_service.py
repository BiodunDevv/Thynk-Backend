import httpx

from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.services.ai.base import AIProviderBase


class AzureOpenAIService(AIProviderBase):
    async def generate_prompt(self, prompt: str) -> dict:
        settings = get_settings()
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            return {
                "content": f"Thynk enhanced prompt:\n\n{prompt}\n\nAdd clear goals, constraints, and expected output.",
                "model": "mock-azure-openai",
                "token_usage": 0,
            }

        endpoint = settings.azure_openai_endpoint.rstrip("/")
        url = (
            f"{endpoint}/openai/deployments/"
            f"{settings.azure_openai_deployment_name}/chat/completions"
        )
        params = {"api-version": settings.azure_openai_api_version}
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are Thynk's AI prompt enhancement engine. Return polished, high-quality prompt output.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": settings.azure_openai_max_tokens,
            "temperature": 0.7,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    params=params,
                    headers={
                        "api-key": settings.azure_openai_api_key,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                usage = data.get("usage", {})
                return {
                    "content": text,
                    "model": settings.azure_openai_model_name,
                    "token_usage": usage.get("total_tokens"),
                }
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise AppException(
                    502,
                    "Azure OpenAI rejected the request. Please check the API key, endpoint, deployment, and API version.",
                    ErrorCodes.PROMPT_GENERATION_FAILED,
                    details={"provider": "azure_openai", "status_code": 401},
                ) from exc
            if exc.response.status_code == 404:
                raise AppException(
                    502,
                    "Azure OpenAI deployment was not found. Please confirm the deployment name and endpoint.",
                    ErrorCodes.PROMPT_GENERATION_FAILED,
                    details={"provider": "azure_openai", "status_code": 404},
                ) from exc
            if exc.response.status_code == 429:
                raise AppException(
                    503,
                    "Azure OpenAI is rate limiting requests. Please try again shortly.",
                    ErrorCodes.SERVICE_UNAVAILABLE,
                    details={"provider": "azure_openai", "status_code": 429},
                ) from exc
            raise AppException(
                502,
                "Azure OpenAI returned an unexpected error.",
                ErrorCodes.PROMPT_GENERATION_FAILED,
                details={"provider": "azure_openai", "status_code": exc.response.status_code},
            ) from exc
        except httpx.TimeoutException as exc:
            raise AppException(
                504,
                "Azure OpenAI took too long to respond.",
                ErrorCodes.SERVICE_UNAVAILABLE,
                details={"provider": "azure_openai"},
            ) from exc
        except httpx.HTTPError as exc:
            raise AppException(
                502,
                "Unable to reach Azure OpenAI.",
                ErrorCodes.SERVICE_UNAVAILABLE,
                details={"provider": "azure_openai"},
            ) from exc
