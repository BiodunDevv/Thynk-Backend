from app.core.constants import PromptCategory
from app.models.prompt_template import PromptTemplate


async def seed_templates() -> None:
    records = [
        {
            "title": "Landing Page UX Brief",
            "description": "Generate a product-focused UX brief for a modern landing page.",
            "category": PromptCategory.DESIGN,
            "template_content": "Create a UX brief for a responsive landing page with clear goals, audience, information hierarchy, conversion points, and PWA-friendly interaction guidance.",
            "tags": ["design", "ux", "landing-page"],
        },
        {
            "title": "API Integration Task Prompt",
            "description": "Generate a detailed implementation prompt for backend integration tasks.",
            "category": PromptCategory.DEVELOPMENT,
            "template_content": "Create a technical prompt that defines APIs, edge cases, testing scope, and rollout notes for a backend integration task.",
            "tags": ["development", "backend", "api"],
        },
    ]
    for item in records:
        exists = await PromptTemplate.find_one(PromptTemplate.title == item["title"])
        if not exists:
            await PromptTemplate(**item).insert()
