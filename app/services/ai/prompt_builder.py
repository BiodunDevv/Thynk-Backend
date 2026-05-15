from app.api.v1.prompts.schemas import GeneratePromptRequest


def build_prompt_instruction(payload: GeneratePromptRequest) -> str:
    return (
        f"Create a {payload.complexity.value} prompt for {payload.platform.value} "
        f"in a {payload.tone.value} tone for the {payload.category.value} category. "
        f"Output format: {payload.output_format.value}. User idea: {payload.rough_input}"
    )


def build_enhancement_instruction(
    rough_input: str,
    category: str,
    tone: str,
    platform: str,
    complexity: str,
    output_format: str,
) -> str:
    return (
        "Rewrite the user's rough idea into a clean, structured brief for downstream AI prompt generation. "
        "Preserve meaning, remove ambiguity, and make it easy for an AI model to understand. "
        f"Category: {category}. Tone: {tone}. Platform: {platform}. Complexity: {complexity}. "
        f"Output format target: {output_format}. Raw user idea: {rough_input}"
    )


def build_generation_instruction_from_enhanced(
    enhanced_input: str,
    category: str,
    tone: str,
    platform: str,
    complexity: str,
    output_format: str,
) -> str:
    return (
        f"Create a {complexity} prompt for {platform} "
        f"in a {tone} tone for the {category} category. "
        f"Output format: {output_format}. Use this clarified brief: {enhanced_input}"
    )
