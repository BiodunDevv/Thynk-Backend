from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.prompts.schemas import (
    GeneratePromptRequest,
    PromptGenerationResult,
    PromptResponse,
    TestAIRequest,
    TestAIResponse,
)
from app.api.v1.prompts.service import generate_prompt, list_prompts, test_ai_provider
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/prompts", tags=["Prompt Generation", "Saved Prompts"])


@router.post("/generate", response_model=SuccessResponse[PromptGenerationResult], summary="Generate AI-enhanced prompt", description="Generates a polished AI prompt, enforces plan usage, and optionally saves the result.")
async def create_prompt(payload: GeneratePromptRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Prompt generated successfully.", data=await generate_prompt(user, payload))


@router.post("/test-ai", response_model=SuccessResponse[TestAIResponse], summary="Test AI provider", description="Sends a raw prompt to the currently configured AI provider without consuming prompt credits or saving a prompt.")
async def test_ai(payload: TestAIRequest):
    return SuccessResponse(message="AI provider test completed successfully.", data=await test_ai_provider(payload.prompt))


@router.get("/me", response_model=SuccessResponse[list[PromptResponse]], summary="List saved prompts", description="Returns the logged-in user's saved prompts.")
async def my_prompts(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Prompts fetched successfully.", data=await list_prompts(user))
