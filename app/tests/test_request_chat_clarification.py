from unittest.mock import AsyncMock

import pytest

from app.api.v1.request_chats.schemas import RequestChatCreateRequest, RequestChatMessagePayload
from app.api.v1.request_chats.service import add_message, create_chat
from app.core.constants import RequestChatSource
from app.core.error_codes import ErrorCodes
from app.core.exceptions import AppException
from app.models.request_chat import RequestChat, RequestChatMessage
from app.models.user import User
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


def test_clarification_result_normalizes_next_action_aliases():
    result = ClarificationResult.model_validate(
        {
            "clarification_complete": False,
            "next_action": "ask_questions",
            "questions": [
                {
                    "type": "open",
                    "question": "What does your SaaS product do?",
                }
            ],
        }
    )

    assert result.next_action == "ask_followup"
    assert result.questions[0].question == "What does your SaaS product do?"


def test_clarification_result_allows_only_one_question():
    with pytest.raises(Exception):
        ClarificationResult.model_validate(
            {
                "clarification_complete": False,
                "next_action": "ask_followup",
                "questions": [
                    {"type": "open", "question": "Question one?"},
                    {"type": "open", "question": "Question two?"},
                ],
            }
        )


@pytest.mark.asyncio
async def test_create_chat_does_not_insert_when_clarification_fails(monkeypatch):
    insert_mock = AsyncMock()
    clarification_mock = AsyncMock(
        side_effect=AppException(
            502,
            "Thynk could not generate clarification questions right now.",
            ErrorCodes.PROMPT_GENERATION_FAILED,
        )
    )
    monkeypatch.setattr(
        "app.api.v1.request_chats.service.generate_clarification_for_chat",
        clarification_mock,
    )

    class FakeChat:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.id = "chat_123"
            self.messages = kwargs.get("messages", [])

        async def insert(self):
            await insert_mock()

    monkeypatch.setattr("app.api.v1.request_chats.service.RequestChat", FakeChat)

    user = User.model_construct(id="user_123")
    payload = RequestChatCreateRequest(
        title="Landing page prompt",
        category="marketing",
        message="Help me create a landing page prompt.",
        source=RequestChatSource.ASSISTANT_CHAT,
    )

    with pytest.raises(AppException) as exc:
        await create_chat(user, payload)

    assert exc.value.error_code == ErrorCodes.PROMPT_GENERATION_FAILED
    insert_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_message_answers_follow_up_after_final_prompt(monkeypatch):
    chat = make_chat(
        RequestChatMessage(
            id="u1",
            role="user",
            content="Create a landing page prompt.",
            metadata={},
            created_at=utc_now(),
        ),
        RequestChatMessage(
            id="f1",
            role="assistant",
            content="## Prompt\n\nYou are a senior marketer...",
            metadata={"is_final": True},
            created_at=utc_now(),
        ),
    )
    chat.id = "chat_123"
    save_mock = AsyncMock()

    monkeypatch.setattr("app.api.v1.request_chats.service.RequestChat.get", AsyncMock(return_value=chat))
    monkeypatch.setattr(RequestChat, "save", save_mock)

    ai_service = type(
        "FakeAIService",
        (),
        {
            "generate_prompt": AsyncMock(
                return_value={"content": "Use the hero section to lead with the product value.", "model": "test-model", "token_usage": 42}
            )
        },
    )()
    monkeypatch.setattr("app.services.ai.base.get_ai_service", lambda: ai_service)

    user = User.model_construct(id="user_123")
    updated = await add_message(
        user,
        "chat_123",
        RequestChatMessagePayload(content="How should I improve the hero section?"),
    )

    assert updated.messages[-1].metadata["type"] == "follow_up_answer"
    assert updated.messages[-1].content == "Use the hero section to lead with the product value."
    save_mock.assert_awaited()
