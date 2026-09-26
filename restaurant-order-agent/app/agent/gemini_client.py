from __future__ import annotations

from google import genai
from google.genai import types

from app.agent.llm_types import Message, ModelTurn, TextBlock, ToolResultBlock, ToolUseBlock

MAX_OUTPUT_TOKENS = 1024


class GeminiLLMClient:
    """Thin wrapper around the Gemini SDK that speaks in this project's own
    ModelTurn/ContentBlock/Message types, so the rest of the agent code
    never touches the SDK's request/response objects directly (and can be
    swapped for a fake client in tests, or for another provider later)."""

    def __init__(self, api_key: str, model: str):
        # The SDK validates the key eagerly, so building the client is
        # deferred to the first real call — this lets the app import/start
        # even before GEMINI_API_KEY is configured (e.g. in tests or before
        # first setup).
        self._api_key = api_key
        self._model = model
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def create_turn(self, system: str, messages: list[Message], tools: list[dict]) -> ModelTurn:
        contents = [_message_to_content(message) for message in messages]
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            tools=[_to_gemini_tool(tools)] if tools else None,
        )

        response = self._get_client().models.generate_content(
            model=self._model, contents=contents, config=config
        )

        parts = response.candidates[0].content.parts or []
        content: list[TextBlock | ToolUseBlock] = []
        has_tool_use = False
        for index, part in enumerate(parts):
            if part.function_call is not None:
                has_tool_use = True
                call_id = part.function_call.id or f"call_{index}"
                content.append(
                    ToolUseBlock(
                        id=call_id,
                        name=part.function_call.name,
                        input=dict(part.function_call.args or {}),
                    )
                )
            elif part.text:
                content.append(TextBlock(text=part.text))

        return ModelTurn(stop_reason="tool_use" if has_tool_use else "end_turn", content=content)


def _to_gemini_tool(tools: list[dict]) -> types.Tool:
    declarations = [
        types.FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters_json_schema=tool["input_schema"],
        )
        for tool in tools
    ]
    return types.Tool(function_declarations=declarations)


def _message_to_content(message: Message) -> types.Content:
    parts: list[types.Part] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            parts.append(types.Part.from_text(text=block.text))
        elif isinstance(block, ToolUseBlock):
            parts.append(types.Part.from_function_call(name=block.name, args=block.input))
        elif isinstance(block, ToolResultBlock):
            parts.append(
                types.Part.from_function_response(
                    name=block.name, response={"result": block.content}
                )
            )
    return types.Content(role=message.role, parts=parts)
