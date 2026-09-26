from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingMessage:
    from_number: str
    text: str
    message_id: str


def verify_webhook(mode: str | None, token: str | None, challenge: str | None, expected_token: str) -> str | None:
    """Implements Meta's webhook verification handshake (GET request with
    hub.mode / hub.verify_token / hub.challenge query params)."""
    if mode == "subscribe" and token == expected_token and challenge is not None:
        return challenge
    return None


def parse_incoming_messages(payload: dict) -> list[IncomingMessage]:
    """Extracts text messages from a WhatsApp Cloud API webhook payload.
    Non-text messages (image, audio, etc.) and status updates (sent,
    delivered, read) are ignored for this MVP."""
    messages: list[IncomingMessage] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                body = message.get("text", {}).get("body")
                if not body:
                    continue
                messages.append(
                    IncomingMessage(
                        from_number=message["from"],
                        text=body,
                        message_id=message.get("id", ""),
                    )
                )

    return messages
