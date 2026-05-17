from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


QuestionType = Literal["single", "multi", "yesno", "open"]
NextAction = Literal["ask_followup", "ready_for_final_prompt"]


class ClarificationQuestion(BaseModel):
    type: QuestionType
    question: str = Field(..., min_length=3)
    options: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self) -> "ClarificationQuestion":
        if self.type == "open":
            self.options = []
        elif self.type == "yesno" and not self.options:
            self.options = ["Yes", "No"]
        elif self.type in {"single", "multi"} and len(self.options) < 2:
            raise ValueError("single and multi questions require at least two options")
        return self


class ClarificationResult(BaseModel):
    clarification_complete: bool = False
    next_action: NextAction = "ask_followup"
    questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=1)
    reasoning_summary: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_action_aliases(cls, value):
        if not isinstance(value, dict):
            return value

        next_action = value.get("next_action")
        if isinstance(next_action, str):
            normalized = next_action.strip().lower()
            alias_map = {
                "ask_questions": "ask_followup",
                "ask_question": "ask_followup",
                "follow_up": "ask_followup",
                "followup": "ask_followup",
                "ready": "ready_for_final_prompt",
                "final_prompt": "ready_for_final_prompt",
                "generate_final_prompt": "ready_for_final_prompt",
            }
            value["next_action"] = alias_map.get(normalized, normalized)
        return value

    @model_validator(mode="after")
    def normalize_state(self) -> "ClarificationResult":
        if self.clarification_complete or self.next_action == "ready_for_final_prompt":
            self.clarification_complete = True
            self.next_action = "ready_for_final_prompt"
            self.questions = []
        elif not self.questions:
            raise ValueError("ask_followup results must include at least one question")
        return self
