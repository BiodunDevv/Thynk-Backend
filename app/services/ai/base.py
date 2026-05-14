from abc import ABC, abstractmethod


class AIProviderBase(ABC):
    @abstractmethod
    async def generate_prompt(self, prompt: str) -> dict:
        raise NotImplementedError


def get_ai_service() -> AIProviderBase:
    from app.services.ai.azure_openai_service import AzureOpenAIService

    return AzureOpenAIService()
