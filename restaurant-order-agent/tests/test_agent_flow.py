from app.agent.chat_agent import ChatAgent
from tests.fake_claude import FakeLLMClient, text_turn, tool_turn

PHONE = "5511999999999"


def _agent(fake_llm, menu, faq, restaurant, order_store, session_store):
    return ChatAgent(fake_llm, menu, faq, restaurant, order_store, session_store)


def test_ordering_flow_builds_cart_then_confirms(menu, faq, restaurant, order_store, session_store):
    fake_llm = FakeLLMClient(
        [
            tool_turn("add_item_to_cart", {"item_id": "pizza_margherita_m", "quantity": 2}, "t1"),
            tool_turn("view_cart", {}, "t2"),
            text_turn("Você quer 2x Pizza Margherita (Média), total R$ 85.80. Posso confirmar?"),
        ]
    )
    agent = _agent(fake_llm, menu, faq, restaurant, order_store, session_store)

    reply = agent.handle_message(PHONE, "Quero 2 pizzas margherita média")

    assert "85.80" in reply
    session = session_store.get_or_create(PHONE)
    assert session.cart["pizza_margherita_m"].quantity == 2
    # nothing confirmed yet
    assert order_store.latest_order_for_customer(PHONE) is None


def test_confirm_order_persists_order_and_clears_cart(menu, faq, restaurant, order_store, session_store):
    setup_llm = FakeLLMClient(
        [
            tool_turn("add_item_to_cart", {"item_id": "pizza_margherita_m", "quantity": 2}, "t1"),
            text_turn("Adicionei 2x Margherita ao carrinho."),
        ]
    )
    agent = _agent(setup_llm, menu, faq, restaurant, order_store, session_store)
    agent.handle_message(PHONE, "Quero 2 pizzas margherita média")

    confirm_llm = FakeLLMClient(
        [
            tool_turn("confirm_order", {}, "t2"),
            text_turn("Pedido confirmado, obrigado!"),
        ]
    )
    agent = _agent(confirm_llm, menu, faq, restaurant, order_store, session_store)
    reply = agent.handle_message(PHONE, "Sim, pode confirmar")

    assert reply == "Pedido confirmado, obrigado!"
    order = order_store.latest_order_for_customer(PHONE)
    assert order is not None
    assert order.total() == 85.80
    assert session_store.get_or_create(PHONE).cart == {}


def test_check_order_status_reports_latest_order(menu, faq, restaurant, order_store, session_store):
    setup_llm = FakeLLMClient(
        [
            tool_turn("add_item_to_cart", {"item_id": "agua_mineral", "quantity": 1}, "t1"),
            text_turn("Adicionei uma água."),
        ]
    )
    agent = _agent(setup_llm, menu, faq, restaurant, order_store, session_store)
    agent.handle_message(PHONE, "Quero uma água")

    confirm_llm = FakeLLMClient(
        [
            tool_turn("confirm_order", {}, "t2"),
            text_turn("Pedido confirmado!"),
        ]
    )
    agent = _agent(confirm_llm, menu, faq, restaurant, order_store, session_store)
    agent.handle_message(PHONE, "Confirma o pedido")
    order = order_store.latest_order_for_customer(PHONE)

    status_llm = FakeLLMClient(
        [
            tool_turn("check_order_status", {}, "t3"),
            text_turn(f"Seu pedido #{order.id} está recebido."),
        ]
    )
    agent = _agent(status_llm, menu, faq, restaurant, order_store, session_store)
    reply = agent.handle_message(PHONE, "Cadê meu pedido?")

    assert str(order.id) in reply
    tool_result = session_store.get_or_create(PHONE).history[-2]["content"][0]
    assert "recebido" in tool_result["content"]


def test_unknown_item_does_not_crash_agent(menu, faq, restaurant, order_store, session_store):
    fake_llm = FakeLLMClient(
        [
            tool_turn("add_item_to_cart", {"item_id": "pizza_de_chocolate", "quantity": 1}, "t1"),
            text_turn("Não temos esse item, que tal uma Margherita?"),
        ]
    )
    agent = _agent(fake_llm, menu, faq, restaurant, order_store, session_store)

    reply = agent.handle_message(PHONE, "Quero uma pizza de chocolate")

    assert "Margherita" in reply
    assert session_store.get_or_create(PHONE).cart == {}
