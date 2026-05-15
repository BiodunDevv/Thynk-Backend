from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.templates.schemas import TemplateCreateRequest, TemplateResponse
from app.api.v1.templates.service import create_template, list_templates
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.core.permissions import require_role
from app.core.response import SuccessResponse
from app.models.prompt_template import PromptTemplate

router = APIRouter(prefix="/templates", tags=["Prompt Templates"])
admin_router = APIRouter(prefix="/admin/templates", tags=["Admin Templates"])


@router.get("", response_model=SuccessResponse[list[TemplateResponse]], summary="List prompt templates")
async def browse_templates():
    return SuccessResponse(message="Templates fetched successfully.", data=await list_templates())


@router.get("/{template_id}", response_model=SuccessResponse[TemplateResponse], summary="Get template by ID")
async def get_template(template_id: str):
    t = await PromptTemplate.get(template_id)
    if not t or not t.is_active:
        raise AppException(404, "Template not found.", ErrorCodes.NOT_FOUND if hasattr(ErrorCodes, "NOT_FOUND") else "NOT_FOUND")
    return SuccessResponse(message="Template fetched successfully.", data=TemplateResponse.model_validate(t.model_dump()))


@admin_router.get("", response_model=SuccessResponse[list[TemplateResponse]], summary="List all templates (admin)")
async def admin_list_templates(_=Depends(require_role(role="SUPER_ADMIN"))):
    templates = await PromptTemplate.find_all().sort("-created_at").to_list()
    return SuccessResponse(message="Templates fetched successfully.", data=[TemplateResponse.model_validate(t.model_dump()) for t in templates])


@admin_router.get("/{template_id}", response_model=SuccessResponse[TemplateResponse], summary="Get template by ID (admin)")
async def admin_get_template(template_id: str, _=Depends(require_role(role="SUPER_ADMIN"))):
    t = await PromptTemplate.get(template_id)
    if not t:
        raise AppException(404, "Template not found.", "NOT_FOUND")
    return SuccessResponse(message="Template fetched successfully.", data=TemplateResponse.model_validate(t.model_dump()))


@admin_router.post("", response_model=SuccessResponse[TemplateResponse], status_code=status.HTTP_201_CREATED, summary="Create prompt template")
async def create_admin_template(payload: TemplateCreateRequest, _=Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Template created successfully.", data=await create_template(payload))


@admin_router.patch("/{template_id}/toggle", response_model=SuccessResponse[TemplateResponse], summary="Toggle template active status")
async def toggle_template(template_id: str, _=Depends(require_role(role="SUPER_ADMIN"))):
    t = await PromptTemplate.get(template_id)
    if not t:
        raise AppException(404, "Template not found.", "NOT_FOUND")
    t.is_active = not t.is_active
    await t.save()
    return SuccessResponse(message=f"Template {'activated' if t.is_active else 'deactivated'}.", data=TemplateResponse.model_validate(t.model_dump()))


@admin_router.delete("/{template_id}", response_model=SuccessResponse[dict], status_code=status.HTTP_200_OK, summary="Delete template")
async def delete_template(template_id: str, _=Depends(require_role(role="SUPER_ADMIN"))):
    t = await PromptTemplate.get(template_id)
    if not t:
        raise AppException(404, "Template not found.", "NOT_FOUND")
    await t.delete()
    return SuccessResponse(message="Template deleted successfully.", data={"id": template_id})
