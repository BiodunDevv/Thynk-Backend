from app.api.v1.templates.schemas import TemplateCreateRequest, TemplateResponse
from app.models.prompt_template import PromptTemplate


async def list_templates() -> list[TemplateResponse]:
    templates = await PromptTemplate.find(PromptTemplate.is_active == True).to_list()
    return [TemplateResponse.model_validate(item.model_dump()) for item in templates]


async def create_template(payload: TemplateCreateRequest) -> TemplateResponse:
    template = PromptTemplate(**payload.model_dump())
    await template.insert()
    return TemplateResponse.model_validate(template.model_dump())
