from app.core.config import Settings


def test_azure_openai_base_url_normalizes_foundry_endpoint():
    settings = Settings(
        AZURE_OPENAI_ENDPOINT="https://biodundev.services.ai.azure.com/api/projects/BiodunDev/openai/v1/responses"
    )

    assert settings.azure_openai_base_url == "https://biodundev.services.ai.azure.com/api/projects/BiodunDev/openai/v1"


def test_azure_openai_base_url_preserves_clean_foundry_base():
    settings = Settings(
        AZURE_OPENAI_ENDPOINT="https://biodundev.services.ai.azure.com/openai/v1"
    )

    assert settings.azure_openai_base_url == "https://biodundev.services.ai.azure.com/openai/v1"
