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


ContentBlock = Union[TextBlock, ToolUseBlock]


@dataclass(frozen=True)
class ModelTurn:
    stop_reason: str  # "end_turn" | "tool_use" | other Anthropic stop reasons
    content: list[ContentBlock]

    def text(self) -> str:
        return "\n".join(block.text for block in self.content if isinstance(block, TextBlock))

    def tool_uses(self) -> list[ToolUseBlock]:
        return [block for block in self.content if isinstance(block, ToolUseBlock)]


class LLMClient(Protocol):
    def create_turn(self, system: str, messages: list[dict], tools: list[dict]) -> ModelTurn: ...
