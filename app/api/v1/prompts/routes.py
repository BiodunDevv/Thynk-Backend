from fastapi import APIRouter, Depends, Request

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.prompts.schemas import (
    EnhancePromptRequest,
    EnhancePromptResponse,
    FreeTestRequest,
    FreeTestResponse,
    GeneratePromptRequest,
    PromptGenerationResult,
    PromptResponse,
    TestAIRequest,
    TestAIResponse,
)
from app.api.v1.prompts.service import (
    enhance_prompt_input,
    free_test_generate,
    generate_prompt,
    list_prompts,
    test_ai_provider,
)
from app.core.response import SuccessResponse
from app.models.user import User

router = APIRouter(prefix="/prompts", tags=["Prompt Generation", "Saved Prompts"])


@router.post("/generate", response_model=SuccessResponse[PromptGenerationResult], summary="Generate AI-enhanced prompt", description="Generates a polished AI prompt, enforces plan usage, and optionally saves the result.")
async def create_prompt(payload: GeneratePromptRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Prompt generated successfully.", data=await generate_prompt(user, payload))


@router.post("/enhance", response_model=SuccessResponse[EnhancePromptResponse], summary="Enhance rough prompt input", description="Cleans and structures the user's rough idea into a clearer AI-ready brief before final prompt generation.")
async def enhance_prompt(payload: EnhancePromptRequest, user: User = Depends(get_current_user)):
    return SuccessResponse(message="Prompt input enhanced successfully.", data=await enhance_prompt_input(payload))


@router.post("/test-ai", response_model=SuccessResponse[TestAIResponse], summary="Test AI provider", description="Sends a raw prompt to the currently configured AI provider without consuming prompt credits or saving a prompt.")
async def test_ai(payload: TestAIRequest):
    result = await test_ai_provider(payload.prompt, payload.images)
    return SuccessResponse(message="AI provider test completed successfully.", data=result)


@router.post("/test-free", response_model=SuccessResponse[FreeTestResponse], summary="Free test generation", description="Anonymous 1-time free test generation — no auth required.")
async def test_free(payload: FreeTestRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    result = await free_test_generate(payload.prompt, client_ip)
    return SuccessResponse(message="Free test completed.", data=FreeTestResponse(**result))


@router.get("/me", response_model=SuccessResponse[list[PromptResponse]], summary="List saved prompts", description="Returns the logged-in user's saved prompts.")
async def my_prompts(user: User = Depends(get_current_user)):
    return SuccessResponse(message="Prompts fetched successfully.", data=await list_prompts(user))
