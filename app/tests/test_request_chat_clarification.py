from app.core.constants import RequestChatSource
from app.models.request_chat import RequestChat, RequestChatMessage
from app.services.ai.clarification_service import (
    build_chat_state,
    build_generation_context,
    build_clarification_metadata,
    fallback_clarification,
)
from app.services.ai.clarification_types import ClarificationResult
from app.utils.datetime import utc_now


def make_chat(*messages: RequestChatMessage) -> RequestChat:
    return RequestChat.model_construct(
        user_id="user_123",
        title="Landing page prompt",
        category="marketing",
        source=RequestChatSource.ASSISTANT_CHAT,
        messages=list(messages),
        generated_prompt_ids=[],
        is_favorite=False,
        is_reported=False,
        reported_reason=None,
        deleted_at=None,
        admin_notes=[],
    )


def test_fallback_clarification_asks_for_audience_when_context_is_thin():
    chat = make_chat(
        RequestChatMessage(
            id="m1",
            role="user",
            content="Help me create a landing page prompt.",
            metadata={},
            created_at=utc_now(),
        )
    )

    result = fallback_clarification(chat)

    assert result.clarification_complete is False
    assert result.next_action == "ask_followup"
    assert result.questions
    assert "Who is this prompt mainly for?" == result.questions[0].question


def test_fallback_clarification_marks_ready_after_multiple_rounds():
    chat = make_chat(
        RequestChatMessage(
            id="u1",
            role="user",
            content="Help me create a prompt for a fintech onboarding flow.",
            metadata={},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="a1",
            role="assistant",
            content="Who is this for?",
            metadata={"type": "clarification"},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="u2",
            role="user",
            content="It is for internal product designers.",
            metadata={},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="a2",
            role="assistant",
            content="What kind of output do you need?",
            metadata={"type": "clarification"},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="u3",
            role="user",
            content="A polished prompt with examples and constraints.",
            metadata={},
            created_at=utc_now(),
        ),
    )

    result = fallback_clarification(chat)

    assert result.clarification_complete is True
    assert result.next_action == "ready_for_final_prompt"
    assert result.questions == []


def test_build_chat_state_tracks_clarification_and_image_context():
    chat = make_chat(
        RequestChatMessage(
            id="u1",
            role="user",
            content="Draft a campaign prompt",
            metadata={"image_urls": ["https://example.com/reference.png"]},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="a1",
            role="assistant",
            content="Who is this for?",
            metadata={"type": "clarification", "clarification_complete": False, "next_action": "ask_followup"},
            created_at=utc_now(),
        ),
    )

    state = build_chat_state(chat)

    assert state["has_images"] is True
    assert state["clarification_turn_count"] == 1
    assert state["latest_user_message"] == "Draft a campaign prompt"
    assert state["conversation"][1]["type"] == "clarification"


def test_build_generation_context_includes_clarification_answers():
    chat = make_chat(
        RequestChatMessage(
            id="u1",
            role="user",
            content="Help me create a product launch prompt.",
            metadata={},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="a1",
            role="assistant",
            content="Who is this for?",
            metadata={
                "type": "clarification",
                "clarification": {
                    "clarification_complete": False,
                    "next_action": "ask_followup",
                    "questions": [
                        {"type": "single", "question": "Who is this for?", "options": ["Users", "Investors"]}
                    ],
                },
            },
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="u2",
            role="user",
            content="It is for internal product marketers.",
            metadata={},
            created_at=utc_now(),
        ),
    )

    context = build_generation_context(chat)

    assert "Clarification summary:" in context
    assert "Question: Who is this for?" in context
    assert "Answer: It is for internal product marketers." in context


def test_build_clarification_metadata_contains_structured_payload():
    result = ClarificationResult(
        clarification_complete=False,
        next_action="ask_followup",
        reasoning_summary="The target audience is still unclear.",
        questions=[
            {
                "type": "single",
                "question": "Who is this mainly for?",
                "options": ["Me", "My team"],
            }
        ],
    )

    metadata = build_clarification_metadata(result)

    assert metadata["type"] == "clarification"
    assert metadata["clarification_complete"] is False
    assert metadata["next_action"] == "ask_followup"
    assert metadata["clarification"]["questions"][0]["question"] == "Who is this mainly for?"
