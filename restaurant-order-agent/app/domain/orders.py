from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class OrderStatus(str, Enum):
    RECEIVED = "recebido"
    PREPARING = "em_preparo"
    OUT_FOR_DELIVERY = "saiu_para_entrega"
    DELIVERED = "entregue"
    CANCELLED = "cancelado"

    def label_pt(self) -> str:
        return {
            OrderStatus.RECEIVED: "recebido",
            OrderStatus.PREPARING: "em preparo",
            OrderStatus.OUT_FOR_DELIVERY: "saiu para entrega",
            OrderStatus.DELIVERED: "entregue",
            OrderStatus.CANCELLED: "cancelado",
        }[self]


@dataclass(frozen=True)
class OrderItem:
    item_id: str
    name: str
    unit_price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class Order:
    id: int
    customer_phone: str
    items: list[OrderItem]
    status: OrderStatus
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def total(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)


class OrderStore:
    """SQLite-backed persistence for orders. One row per order; items are
    stored as JSON since they are never queried individually."""

    def __init__(self, db_path: Path | str):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_phone TEXT NOT NULL,
                    items TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_order(self, customer_phone: str, items: list[OrderItem]) -> Order:
        created_at = datetime.now(timezone.utc).isoformat()
        items_json = json.dumps([item.__dict__ for item in items])
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO orders (customer_phone, items, status, created_at) "
                "VALUES (?, ?, ?, ?)",
                (customer_phone, items_json, OrderStatus.RECEIVED.value, created_at),
            )
            order_id = cursor.lastrowid
        return Order(
            id=order_id,
            customer_phone=customer_phone,
            items=items,
            status=OrderStatus.RECEIVED,
            created_at=created_at,
        )

    def get_order(self, order_id: int) -> Order | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return self._row_to_order(row) if row else None

    def latest_order_for_customer(self, customer_phone: str) -> Order | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE customer_phone = ? "
                "ORDER BY id DESC LIMIT 1",
                (customer_phone,),
            ).fetchone()
        return self._row_to_order(row) if row else None

    def update_status(self, order_id: int, status: OrderStatus) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?", (status.value, order_id)
            )
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_order(row: sqlite3.Row) -> Order:
        items = [OrderItem(**entry) for entry in json.loads(row["items"])]
        return Order(
            id=row["id"],
            customer_phone=row["customer_phone"],
            items=items,
            status=OrderStatus(row["status"]),
            created_at=row["created_at"],
        )
