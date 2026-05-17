import json
import logging

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.services.ai.base import AIProviderBase
from app.services.ai.clarification_types import ClarificationResult

logger = logging.getLogger(__name__)


def _safe_response_body(exc: APIStatusError) -> str:
    body = exc.response.text.strip()
    return body[:4000] if body else "<empty>"


def _log_upstream_failure(
    *,
    stage: str,
    endpoint: str,
    deployment: str,
    exc: Exception,
    request_id: str | None = None,
) -> None:
    if isinstance(exc, APIStatusError):
        request_id = request_id or exc.response.headers.get("x-request-id") or exc.response.headers.get("apim-request-id")
        logger.error(
            "azure_openai_request_failed stage=%s provider=azure_openai endpoint=%s deployment=%s status_code=%s request_id=%s response_body=%s",
            stage,
            endpoint,
            deployment,
            exc.status_code,
            request_id or "-",
            _safe_response_body(exc),
        )
        return

    logger.error(
        "azure_openai_request_failed stage=%s provider=azure_openai endpoint=%s deployment=%s error=%s",
        stage,
        endpoint,
        deployment,
        repr(exc),
    )


def _map_api_status_error(
    *,
    stage: str,
    endpoint: str,
    deployment: str,
    exc: APIStatusError,
) -> AppException:
    _log_upstream_failure(stage=stage, endpoint=endpoint, deployment=deployment, exc=exc)
    if exc.status_code == 400:
        raise AppException(
            502,
            "Azure OpenAI rejected the request. Please confirm the Foundry base URL, deployment name, and request format.",
            ErrorCodes.PROMPT_GENERATION_FAILED,
            details={"provider": "azure_openai", "status_code": 400, "stage": stage},
        ) from exc
    if exc.status_code == 401:
        raise AppException(
            502,
            "Azure OpenAI rejected the request. Please check the API key and Foundry endpoint configuration.",
            ErrorCodes.PROMPT_GENERATION_FAILED,
            details={"provider": "azure_openai", "status_code": 401, "stage": stage},
        ) from exc
    if exc.status_code == 404:
        raise AppException(
            502,
            "Azure OpenAI deployment was not found. Please confirm the deployment name and Foundry endpoint.",
            ErrorCodes.PROMPT_GENERATION_FAILED,
            details={"provider": "azure_openai", "status_code": 404, "stage": stage},
        ) from exc
    if exc.status_code == 429:
        raise AppException(
            503,
            "Azure OpenAI is rate limiting requests. Please try again shortly.",
            ErrorCodes.SERVICE_UNAVAILABLE,
            details={"provider": "azure_openai", "status_code": 429, "stage": stage},
        ) from exc
    raise AppException(
        502,
        "Azure OpenAI returned an unexpected error.",
        ErrorCodes.PROMPT_GENERATION_FAILED,
        details={"provider": "azure_openai", "status_code": exc.status_code, "stage": stage},
    ) from exc


class AzureOpenAIService(AIProviderBase):
    def _get_client(self) -> tuple[AsyncOpenAI | None, str, str]:
        settings = get_settings()
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            return None, "", settings.azure_openai_deployment_name

        endpoint = settings.azure_openai_base_url
        client = AsyncOpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=endpoint,
            timeout=30,
        )
        return client, endpoint, settings.azure_openai_deployment_name

    async def _create_chat_completion(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_prompt: str,
        images: list[dict] | None = None,
    ):
        client, endpoint, deployment = self._get_client()
        settings = get_settings()
        if not client:
            return None, endpoint, deployment

        message_content: str | list[dict] = user_prompt
        if images:
            multimodal_content: list[dict] = [{"type": "text", "text": user_prompt}]
            for image in images:
                multimodal_content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image["image_url"],
                            "detail": image.get("detail", "auto"),
                        },
                    }
                )
            message_content = multimodal_content

        try:
            response = await client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_content},
                ],
                max_completion_tokens=settings.azure_openai_max_tokens,
            )
            return response, endpoint, deployment
        except APIStatusError as exc:
            _map_api_status_error(
                stage=stage,
                endpoint=endpoint,
                deployment=deployment,
                exc=exc,
            )
        except APITimeoutError as exc:
            _log_upstream_failure(stage=stage, endpoint=endpoint, deployment=deployment, exc=exc)
            raise AppException(
                504,
                "Azure OpenAI took too long to respond.",
                ErrorCodes.SERVICE_UNAVAILABLE,
                details={"provider": "azure_openai", "stage": stage},
            ) from exc
        except APIConnectionError as exc:
            _log_upstream_failure(stage=stage, endpoint=endpoint, deployment=deployment, exc=exc)
            raise AppException(
                502,
                "Unable to reach Azure OpenAI.",
                ErrorCodes.SERVICE_UNAVAILABLE,
                details={"provider": "azure_openai", "stage": stage},
            ) from exc
        except Exception as exc:
            _log_upstream_failure(stage=stage, endpoint=endpoint, deployment=deployment, exc=exc)
            raise AppException(
                502,
                "Azure OpenAI returned an unexpected error.",
                ErrorCodes.PROMPT_GENERATION_FAILED,
                details={"provider": "azure_openai", "stage": stage},
            ) from exc

    async def generate_prompt(
        self,
        prompt: str,
        images: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        settings = get_settings()
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            return {
                "content": f"Thynk enhanced prompt:\n\n{prompt}\n\nAdd clear goals, constraints, and expected output.",
                "model": "mock-azure-openai",
                "token_usage": 0,
            }

        response, _, deployment = await self._create_chat_completion(
            stage="prompt_generation",
            system_prompt=system_prompt
            or "You are Thynk's AI prompt enhancement engine. Return polished, high-quality prompt output.",
            user_prompt=prompt,
            images=images,
        )
        text = response.choices[0].message.content if response and response.choices else ""
        usage = response.usage if response else None
        return {
            "content": text or "",
            "model": deployment,
            "token_usage": getattr(usage, "total_tokens", None),
        }

    async def generate_clarification(self, chat_state: dict, images: list[dict] | None = None) -> dict:
        settings = get_settings()

        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            return ClarificationResult(
                clarification_complete=False,
                next_action="ask_followup",
                reasoning_summary="AI provider is not configured, so a safe clarification fallback was used.",
                questions=[
                    {
                        "type": "single",
                        "question": "What would you like Thynk to sharpen first?",
                        "options": [
                            "The audience",
                            "The output format",
                            "The tone",
                            "The technical depth",
                        ],
                    }
                ],
            ).model_dump()

        result = await self.generate_prompt(
            prompt=json.dumps(chat_state, ensure_ascii=False, indent=2),
            images=images,
            system_prompt=(
                "You are Thynk's clarification engine. Decide whether the conversation needs follow-up questions "
                "before generating a final prompt. Return JSON only with keys: clarification_complete, next_action, "
                "questions, reasoning_summary. If questions are needed, return exactly 1 focused question using types "
                "single, multi, yesno, or open. If enough context already exists, set clarification_complete to true "
                "and next_action to ready_for_final_prompt. If images are attached and the user has not specified whether "
                "to follow their visual style, palette, or composition, prioritize one clarification question about how the image "
                "should influence the final prompt."
            ),
        )
        try:
            return ClarificationResult.model_validate_json(result.get("content", "")).model_dump()
        except Exception as exc:
            logger.warning(
                "azure_openai_clarification_parse_failed provider=azure_openai stage=clarification content=%s",
                (result.get("content", "") or "")[:2000],
            )
            raise AppException(
                502,
                "Thynk could not generate clarification questions right now.",
                ErrorCodes.PROMPT_GENERATION_FAILED,
                details={"provider": "azure_openai", "stage": "clarification", "reason": "invalid_json"},
            ) from exc
