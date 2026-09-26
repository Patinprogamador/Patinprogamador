from __future__ import annotations

from dataclasses import dataclass, field

from app.agent.llm_types import Message


@dataclass
class CartItem:
    item_id: str
    quantity: int


@dataclass
class ConversationSession:
    """Per-customer state kept between WhatsApp messages: the running LLM
    message history (so the agent remembers the conversation) and the cart
    being assembled before it becomes a confirmed Order."""

    history: list[Message] = field(default_factory=list)
    cart: dict[str, CartItem] = field(default_factory=dict)

    def add_to_cart(self, item_id: str, quantity: int) -> None:
        existing = self.cart.get(item_id)
        if existing:
            existing.quantity += quantity
        else:
            self.cart[item_id] = CartItem(item_id=item_id, quantity=quantity)

    def remove_from_cart(self, item_id: str, quantity: int | None = None) -> bool:
        existing = self.cart.get(item_id)
        if not existing:
            return False
        if quantity is None or quantity >= existing.quantity:
            del self.cart[item_id]
        else:
            existing.quantity -= quantity
        return True

    def clear_cart(self) -> None:
        self.cart.clear()


class SessionStore:
    """In-memory session storage keyed by customer phone number.

    This is intentionally simple for the MVP: state lives only for the
    lifetime of the process. For a production deployment with more than one
    worker process, replace this with a shared store (e.g. Redis) so all
    workers see the same cart/history for a given customer.
    """

    def __init__(self):
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, customer_phone: str) -> ConversationSession:
        if customer_phone not in self._sessions:
            self._sessions[customer_phone] = ConversationSession()
        return self._sessions[customer_phone]
