from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.templates.schemas import TemplateCreateRequest, TemplateResponse
from app.api.v1.templates.service import create_template, list_templates
from app.core.permissions import require_role
from app.core.response import SuccessResponse

router = APIRouter(prefix="/templates", tags=["Prompt Templates"])
admin_router = APIRouter(prefix="/admin/templates", tags=["Admin Templates"])


@router.get("", response_model=SuccessResponse[list[TemplateResponse]], summary="List prompt templates", description="Returns active prompt templates available to users.")
async def browse_templates():
    return SuccessResponse(message="Templates fetched successfully.", data=await list_templates())


@admin_router.post("", response_model=SuccessResponse[TemplateResponse], status_code=status.HTTP_201_CREATED, summary="Create prompt template", description="Creates a new prompt template. Requires Bearer token with SUPER_ADMIN role.")
async def create_admin_template(payload: TemplateCreateRequest, _=Depends(require_role(role="SUPER_ADMIN"))):
    return SuccessResponse(message="Template created successfully.", data=await create_template(payload))
