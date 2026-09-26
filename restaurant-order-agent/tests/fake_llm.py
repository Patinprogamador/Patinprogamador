"""A scripted, offline stand-in for the Gemini client so agent-flow tests
don't need GEMINI_API_KEY or network access. You hand it a fixed sequence
of ModelTurns; it returns them one by one regardless of what the agent asks,
same pattern used for the fake LLM provider in the ESG Risk Screener repo."""

from __future__ import annotations

from app.agent.llm_types import Message, ModelTurn, TextBlock, ToolUseBlock


class FakeLLMClient:
    def __init__(self, turns: list[ModelTurn]):
        self._turns = list(turns)
        self.calls: list[dict] = []

    def create_turn(self, system: str, messages: list[Message], tools: list[dict]) -> ModelTurn:
        self.calls.append({"system": system, "messages": messages, "tools": tools})
        if not self._turns:
            raise AssertionError("FakeLLMClient ran out of scripted turns")
        return self._turns.pop(0)


def text_turn(text: str) -> ModelTurn:
    return ModelTurn(stop_reason="end_turn", content=[TextBlock(text=text)])


def tool_turn(name: str, tool_input: dict, tool_use_id: str = "tool_1") -> ModelTurn:
    return ModelTurn(
        stop_reason="tool_use",
        content=[ToolUseBlock(id=tool_use_id, name=name, input=tool_input)],
    )
