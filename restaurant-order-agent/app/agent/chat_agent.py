from __future__ import annotations

from app.agent.llm_types import LLMClient, Message, TextBlock, ToolResultBlock
from app.agent.prompts import build_system_prompt
from app.agent.tools import TOOL_SCHEMAS, ToolExecutor
from app.domain.menu import Menu
from app.domain.orders import OrderStore
from app.domain.restaurant import FaqEntry, RestaurantInfo
from app.session_store import SessionStore

MAX_TOOL_ITERATIONS = 6
FALLBACK_REPLY = "Desculpe, tive um problema para processar seu pedido. Pode tentar novamente?"


class ChatAgent:
    """Orchestrates a single WhatsApp message through the LLM, running the
    tool-use loop (the model may call several tools in sequence before
    producing a final text reply) and keeping per-customer conversation
    state in the session store."""

    def __init__(
        self,
        llm_client: LLMClient,
        menu: Menu,
        faq: list[FaqEntry],
        restaurant: RestaurantInfo,
        order_store: OrderStore,
        session_store: SessionStore,
    ):
        self._llm_client = llm_client
        self._menu = menu
        self._faq = faq
        self._restaurant = restaurant
        self._order_store = order_store
        self._session_store = session_store
        self._system_prompt = build_system_prompt(restaurant, menu, faq)

    def handle_message(self, customer_phone: str, user_text: str) -> str:
        session = self._session_store.get_or_create(customer_phone)
        session.history.append(Message(role="user", content=[TextBlock(text=user_text)]))

        for _ in range(MAX_TOOL_ITERATIONS):
            turn = self._llm_client.create_turn(
                system=self._system_prompt,
                messages=session.history,
                tools=TOOL_SCHEMAS,
            )

            if turn.stop_reason != "tool_use":
                reply = turn.text().strip() or "Desculpe, não entendi. Pode repetir?"
                session.history.append(Message(role="model", content=[TextBlock(text=reply)]))
                return reply

            session.history.append(Message(role="model", content=turn.content))

            executor = ToolExecutor(self._menu, self._order_store, session, customer_phone)
            tool_results = [
                ToolResultBlock(
                    tool_use_id=tool_use.id,
                    name=tool_use.name,
                    content=executor.execute(tool_use.name, tool_use.input),
                )
                for tool_use in turn.tool_uses()
            ]
            session.history.append(Message(role="user", content=tool_results))

        return FALLBACK_REPLY
