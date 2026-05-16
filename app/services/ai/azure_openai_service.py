import json

import httpx

from app.core.config import get_settings
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.services.ai.base import AIProviderBase
from app.services.ai.clarification_types import ClarificationResult


class AzureOpenAIService(AIProviderBase):
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

        endpoint = settings.azure_openai_endpoint.rstrip("/")
        url = (
            f"{endpoint}/openai/deployments/"
            f"{settings.azure_openai_deployment_name}/chat/completions"
        )
        params = {"api-version": settings.azure_openai_api_version}
        user_content: list[dict] = [{"type": "text", "text": prompt}]
        for image in images or []:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image["image_url"],
                        "detail": image.get("detail", "auto"),
                    },
                }
            )

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    or "You are Thynk's AI prompt enhancement engine. Return polished, high-quality prompt output.",
                },
                {"role": "user", "content": user_content},
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

    async def generate_clarification(self, chat_state: dict) -> dict:
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

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import AzureChatOpenAI
        except ImportError:
            result = await self.generate_prompt(
                prompt=json.dumps(chat_state, ensure_ascii=False, indent=2),
                system_prompt=(
                    "You are Thynk's clarification engine. Decide whether the conversation needs follow-up questions "
                    "before generating a final prompt. Return JSON only with keys: clarification_complete, next_action, "
                    "questions, reasoning_summary. If questions are needed, return 1-2 focused questions using types "
                    "single, multi, yesno, or open."
                ),
            )
            try:
                return ClarificationResult.model_validate_json(result.get("content", "")).model_dump()
            except Exception:
                return ClarificationResult(
                    clarification_complete=False,
                    next_action="ask_followup",
                    reasoning_summary="LangChain is unavailable, so a fallback clarification response was returned.",
                    questions=[
                        {
                            "type": "open",
                            "question": "What outcome do you want this prompt to achieve?",
                        }
                    ],
                ).model_dump()

        llm = AzureChatOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_deployment_name,
            temperature=0.2,
            max_tokens=settings.azure_openai_max_tokens,
        )

        structured_llm = llm.with_structured_output(ClarificationResult)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are Thynk's clarification engine. Read the full chat state and decide whether "
                    "follow-up questions are still needed before generating the final prompt. "
                    "Ask at most two focused questions. Prefer structured, practical questions that reduce ambiguity. "
                    "If enough context already exists, mark clarification_complete true and next_action ready_for_final_prompt.",
                ),
                (
                    "human",
                    "Chat state:\n{chat_state}",
                ),
            ]
        )

        try:
            chain = prompt | structured_llm
            result = await chain.ainvoke(
                {"chat_state": json.dumps(chat_state, ensure_ascii=False, indent=2)}
            )
            if isinstance(result, ClarificationResult):
                return result.model_dump()
            return ClarificationResult.model_validate(result).model_dump()
        except Exception as exc:
            raise AppException(
                502,
                "Thynk could not generate clarification questions right now.",
                ErrorCodes.PROMPT_GENERATION_FAILED,
                details={"provider": "azure_openai", "stage": "clarification"},
            ) from exc
