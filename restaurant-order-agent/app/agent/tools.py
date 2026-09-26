from __future__ import annotations

from app.domain.menu import Menu
from app.domain.orders import OrderItem, OrderStore
from app.session_store import ConversationSession

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "add_item_to_cart",
        "description": (
            "Adiciona um item do cardápio ao carrinho do cliente. Use o "
            "'id' exato do item conforme listado no cardápio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "id do item no cardápio"},
                "quantity": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "quantidade desejada (padrão 1)",
                },
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "remove_item_from_cart",
        "description": "Remove (total ou parcialmente) um item do carrinho do cliente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "id do item no cardápio"},
                "quantity": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "quantidade a remover; se omitido, remove tudo desse item",
                },
            },
            "required": ["item_id"],
        },
    },
    {
        "name": "view_cart",
        "description": "Mostra os itens atualmente no carrinho do cliente e o total.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "confirm_order",
        "description": (
            "Confirma o pedido com os itens atuais do carrinho, criando um "
            "pedido oficial. Só use depois que o cliente confirmar "
            "explicitamente os itens e o total."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_order_status",
        "description": (
            "Consulta o status de um pedido. Se 'order_id' não for informado, "
            "consulta o pedido mais recente desse cliente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "número do pedido"},
            },
        },
    },
]


class ToolExecutor:
    """Executes tool calls against the domain layer for a single customer
    conversation. A fresh instance is created per incoming message, bound to
    that customer's session (cart + history) and phone number."""

    def __init__(
        self,
        menu: Menu,
        order_store: OrderStore,
        session: ConversationSession,
        customer_phone: str,
    ):
        self._menu = menu
        self._order_store = order_store
        self._session = session
        self._customer_phone = customer_phone

    def execute(self, name: str, tool_input: dict) -> str:
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            return f"Ferramenta desconhecida: {name}"
        return handler(tool_input)

    def _tool_add_item_to_cart(self, tool_input: dict) -> str:
        item_id = tool_input["item_id"]
        quantity = int(tool_input.get("quantity", 1))
        item = self._menu.find(item_id)
        if item is None:
            return f"Item '{item_id}' não encontrado no cardápio."
        if quantity < 1:
            return "A quantidade precisa ser pelo menos 1."
        self._session.add_to_cart(item_id, quantity)
        return f"Adicionado: {quantity}x {item.name}.\n\n{self._cart_summary()}"

    def _tool_remove_item_from_cart(self, tool_input: dict) -> str:
        item_id = tool_input["item_id"]
        quantity = tool_input.get("quantity")
        removed = self._session.remove_from_cart(item_id, quantity)
        if not removed:
            return f"O item '{item_id}' não estava no carrinho."
        return f"Removido.\n\n{self._cart_summary()}"

    def _tool_view_cart(self, _tool_input: dict) -> str:
        return self._cart_summary()

    def _tool_confirm_order(self, _tool_input: dict) -> str:
        if not self._session.cart:
            return "O carrinho está vazio. Adicione itens antes de confirmar o pedido."

        order_items = []
        for cart_item in self._session.cart.values():
            item = self._menu.find(cart_item.item_id)
            if item is None:
                continue
            order_items.append(
                OrderItem(
                    item_id=item.id,
                    name=item.name,
                    unit_price=item.price,
                    quantity=cart_item.quantity,
                )
            )

        order = self._order_store.create_order(self._customer_phone, order_items)
        self._session.clear_cart()
        return (
            f"Pedido #{order.id} confirmado! Total: R$ {order.total():.2f}. "
            f"Status atual: {order.status.label_pt()}."
        )

    def _tool_check_order_status(self, tool_input: dict) -> str:
        order_id = tool_input.get("order_id")
        order = (
            self._order_store.get_order(int(order_id))
            if order_id is not None
            else self._order_store.latest_order_for_customer(self._customer_phone)
        )
        if order is None:
            return "Nenhum pedido encontrado para esse cliente."
        if order.customer_phone != self._customer_phone:
            return "Nenhum pedido encontrado para esse cliente."
        return f"Pedido #{order.id}: status = {order.status.label_pt()} (total R$ {order.total():.2f})."

    def _cart_summary(self) -> str:
        if not self._session.cart:
            return "O carrinho está vazio."

        lines = ["Carrinho atual:"]
        total = 0.0
        for cart_item in self._session.cart.values():
            item = self._menu.find(cart_item.item_id)
            if item is None:
                continue
            subtotal = item.price * cart_item.quantity
            total += subtotal
            lines.append(f"- {cart_item.quantity}x {item.name} — R$ {subtotal:.2f}")
        lines.append(f"Total: R$ {total:.2f}")
        return "\n".join(lines)
