"""Local terminal chat with the restaurant agent — no WhatsApp setup needed.

Useful to test/demo the ordering flow while you don't have WhatsApp Cloud
API credentials yet. Requires only ANTHROPIC_API_KEY to be set (in the
environment or in a .env file at the project root).

Usage:
    python scripts/chat_cli.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.anthropic_client import AnthropicLLMClient  # noqa: E402
from app.agent.chat_agent import ChatAgent  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.domain.menu import Menu  # noqa: E402
from app.domain.orders import OrderStore  # noqa: E402
from app.domain.restaurant import RestaurantInfo, load_faq  # noqa: E402
from app.session_store import SessionStore  # noqa: E402

CLI_CUSTOMER_PHONE = "cli-local-user"


def main() -> None:
    settings = get_settings()
    if not settings.anthropic_api_key:
        print("Defina ANTHROPIC_API_KEY no ambiente ou em um arquivo .env antes de rodar.")
        raise SystemExit(1)

    menu = Menu.from_json_file(settings.resolved_menu_path())
    faq = load_faq(settings.resolved_faq_path())
    restaurant = RestaurantInfo(
        name=settings.restaurant_name,
        address=settings.restaurant_address,
        phone=settings.restaurant_phone,
    )
    order_store = OrderStore(settings.resolved_database_path())
    llm_client = AnthropicLLMClient(settings.anthropic_api_key, settings.claude_model)
    agent = ChatAgent(llm_client, menu, faq, restaurant, order_store, SessionStore())

    print(f"Conversando com o agente de {restaurant.name}. Digite 'sair' para encerrar.\n")
    while True:
        try:
            user_text = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_text.lower() in {"sair", "exit", "quit"}:
            break
        if not user_text:
            continue
        reply = agent.handle_message(CLI_CUSTOMER_PHONE, user_text)
        print(f"Agente: {reply}\n")


if __name__ == "__main__":
    main()
