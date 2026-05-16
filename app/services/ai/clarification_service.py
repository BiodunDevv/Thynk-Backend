from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.models.request_chat import RequestChat, RequestChatMessage
from app.services.ai.clarification_types import ClarificationResult


def message_image_urls(message: RequestChatMessage) -> list[str]:
    urls = message.metadata.get("image_urls")
    if isinstance(urls, list):
        return [url for url in urls if isinstance(url, str)]
    return []


def build_chat_state(chat: RequestChat) -> dict[str, Any]:
    user_messages = [message for message in chat.messages if message.role == "user"]
    latest_user_message = user_messages[-1] if user_messages else None
    final_prompt_count = sum(1 for message in chat.messages if message.metadata.get("is_final"))
    clarification_turns = [
        message for message in chat.messages if message.metadata.get("type") == "clarification"
    ]

    return {
        "chat_id": chat.id,
        "title": chat.title,
        "category": chat.category,
        "source": chat.source.value if hasattr(chat.source, "value") else str(chat.source),
        "final_prompt_count": final_prompt_count,
        "clarification_turn_count": len(clarification_turns),
        "has_images": any(message_image_urls(message) for message in chat.messages),
        "latest_user_message": latest_user_message.content if latest_user_message else "",
        "conversation": [
            {
                "role": message.role,
                "content": message.content,
                "type": message.metadata.get("type"),
                "image_count": len(message_image_urls(message)),
                "clarification_complete": message.metadata.get("clarification_complete"),
                "next_action": message.metadata.get("next_action"),
            }
            for message in chat.messages
            if not message.metadata.get("is_final")
        ],
    }


def build_generation_context(chat: RequestChat) -> str:
    user_messages = [message for message in chat.messages if message.role == "user"]
    original_request = user_messages[0].content if user_messages else ""
    latest_request = user_messages[-1].content if user_messages else ""

    lines: list[str] = [
        f"Chat title: {chat.title}",
        f"Category: {chat.category}",
        f"Source: {chat.source.value if hasattr(chat.source, 'value') else chat.source}",
        "",
        "Original user request:",
        original_request,
        "",
    ]

    clarification_pairs = collect_clarification_pairs(chat.messages)
    if clarification_pairs:
        lines.append("Clarification summary:")
        for pair in clarification_pairs:
            lines.append(f"Question: {pair['question']}")
            lines.append(f"Answer: {pair['answer']}")
        lines.append("")

    if latest_request and latest_request != original_request:
        lines.extend(
            [
                "Latest user input:",
                latest_request,
                "",
            ]
        )

    lines.append("Conversation transcript:")

    for message in chat.messages:
        if message.metadata.get("is_final"):
            continue

        role = message.role.upper()
        if message.metadata.get("type") == "clarification":
            clarification = message.metadata.get("clarification")
            if isinstance(clarification, dict) and clarification.get("questions"):
                lines.append(f"{role}: Asked clarification questions.")
                for item in clarification.get("questions", []):
                    question = item.get("question") if isinstance(item, dict) else None
                    if question:
                        lines.append(f"- {question}")
                continue

        lines.append(f"{role}: {message.content}")
        image_urls = message_image_urls(message)
        if image_urls:
            lines.append(f"Attached images: {', '.join(image_urls)}")

    return "\n".join(lines)


def build_clarification_metadata(result: ClarificationResult) -> dict[str, Any]:
    payload = result.model_dump()
    return {
        "type": "clarification",
        "clarification_complete": result.clarification_complete,
        "next_action": result.next_action,
        "clarification": payload,
    }


def fallback_clarification(chat: RequestChat) -> ClarificationResult:
    user_messages = [message.content.strip() for message in chat.messages if message.role == "user"]
    combined = " ".join(user_messages).lower()
    clarification_turns = sum(
        1 for message in chat.messages if message.metadata.get("type") == "clarification"
    )

    if clarification_turns >= 2 or len(user_messages) >= 3 or len(combined) > 220:
        return ClarificationResult(
            clarification_complete=True,
            next_action="ready_for_final_prompt",
            reasoning_summary="Enough context is available to generate the final prompt.",
        )

    if not any(keyword in combined for keyword in ("audience", "customer", "user", "team")):
        return ClarificationResult(
            clarification_complete=False,
            next_action="ask_followup",
            reasoning_summary="Audience is still unclear.",
            questions=[
                {
                    "type": "single",
                    "question": "Who is this prompt mainly for?",
                    "options": [
                        "Myself",
                        "A client or customer",
                        "My team or stakeholders",
                        "A broader public audience",
                    ],
                }
            ],
        )

    return ClarificationResult(
        clarification_complete=False,
        next_action="ask_followup",
        reasoning_summary="The desired output shape still needs clarification.",
        questions=[
            {
                "type": "single",
                "question": "What kind of result do you want Thynk to produce next?",
                "options": [
                    "A polished final prompt",
                    "A structured brief first",
                    "A step-by-step prompt workflow",
                    "A few prompt options to compare",
                ],
            }
        ],
    )


def collect_user_inputs(messages: Iterable[RequestChatMessage]) -> list[str]:
    return [message.content for message in messages if message.role == "user"]


def collect_clarification_pairs(messages: Iterable[RequestChatMessage]) -> list[dict[str, str]]:
    message_list = list(messages)
    pairs: list[dict[str, str]] = []

    for index, message in enumerate(message_list):
        if message.role != "assistant" or message.metadata.get("type") != "clarification":
            continue

        clarification = message.metadata.get("clarification")
        if not isinstance(clarification, dict):
            continue

        questions = clarification.get("questions")
        if not isinstance(questions, list) or not questions:
            continue

        next_user_message = next(
            (
                candidate
                for candidate in message_list[index + 1 :]
                if candidate.role == "user"
            ),
            None,
        )
        if not next_user_message:
            continue

        question_text = questions[0].get("question") if isinstance(questions[0], dict) else None
        if not question_text:
            continue

        pairs.append(
            {
                "question": question_text,
                "answer": next_user_message.content,
            }
        )

    return pairs
