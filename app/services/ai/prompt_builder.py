from app.api.v1.prompts.schemas import GeneratePromptRequest


def build_prompt_instruction(payload: GeneratePromptRequest) -> str:
    return (
        f"Create a {payload.complexity.value} prompt for {payload.platform.value} "
        f"in a {payload.tone.value} tone for the {payload.category.value} category. "
        f"Output format: {payload.output_format.value}. User idea: {payload.rough_input}"
    )
