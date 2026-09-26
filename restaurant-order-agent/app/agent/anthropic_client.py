from __future__ import annotations

import anthropic

from app.agent.llm_types import ModelTurn, TextBlock, ToolUseBlock

MAX_RESPONSE_TOKENS = 1024


class AnthropicLLMClient:
    """Thin wrapper around the Anthropic SDK that speaks in this project's
    own ModelTurn/ContentBlock types, so the rest of the agent code never
    touches the SDK's response objects directly (and can be swapped for a
    fake client in tests)."""

    def __init__(self, api_key: str, model: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def create_turn(self, system: str, messages: list[dict], tools: list[dict]) -> ModelTurn:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=MAX_RESPONSE_TOKENS,
            system=system,
            messages=messages,
            tools=tools,
        )

        content: list[TextBlock | ToolUseBlock] = []
        for block in response.content:
            if block.type == "text":
                content.append(TextBlock(text=block.text))
            elif block.type == "tool_use":
                content.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))

        return ModelTurn(stop_reason=response.stop_reason, content=content)
