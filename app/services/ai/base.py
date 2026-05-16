from abc import ABC, abstractmethod


class AIProviderBase(ABC):
    @abstractmethod
    async def generate_prompt(
        self,
        prompt: str,
        images: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def generate_clarification(
        self,
        chat_state: dict,
        images: list[dict] | None = None,
    ) -> dict:
        raise NotImplementedError


def get_ai_service() -> AIProviderBase:
    from app.services.ai.azure_openai_service import AzureOpenAIService

    return AzureOpenAIService()
