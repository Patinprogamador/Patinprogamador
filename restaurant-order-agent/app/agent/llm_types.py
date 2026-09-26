from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Union


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class ToolUseBlock:
    id: str
    name: str
    input: dict


@dataclass(frozen=True)
class ToolResultBlock:
    tool_use_id: str
    name: str
    content: str


ContentBlock = Union[TextBlock, ToolUseBlock, ToolResultBlock]


@dataclass
class Message:
    """One turn of conversation history, in a representation independent of
    any specific LLM provider's wire format. `role` is "user" or "model"
    (Gemini's own naming — chosen so the Gemini client needs no translation;
    an alternative provider's client would map "model" to whatever it
    expects, e.g. "assistant")."""

    role: str
    content: list[ContentBlock]


@dataclass(frozen=True)
class ModelTurn:
    stop_reason: str  # "end_turn" | "tool_use"
    content: list[ContentBlock]

    def text(self) -> str:
        return "\n".join(block.text for block in self.content if isinstance(block, TextBlock))

    def tool_uses(self) -> list[ToolUseBlock]:
        return [block for block in self.content if isinstance(block, ToolUseBlock)]


class LLMClient(Protocol):
    def create_turn(self, system: str, messages: list[Message], tools: list[dict]) -> ModelTurn: ...
