from __future__ import annotations

import pytest

from app.config import BASE_DIR
from app.domain.menu import Menu
from app.domain.orders import OrderStore
from app.domain.restaurant import RestaurantInfo, load_faq
from app.session_store import SessionStore


@pytest.fixture
def menu() -> Menu:
    return Menu.from_json_file(BASE_DIR / "data" / "menu.json")


@pytest.fixture
def faq():
    return load_faq(BASE_DIR / "data" / "faq.json")


@pytest.fixture
def restaurant() -> RestaurantInfo:
    return RestaurantInfo(
        name="Pizzaria Bella Napoli",
        address="Rua das Palmeiras, 123 - São Paulo, SP",
        phone="(11) 4444-5555",
    )


@pytest.fixture
def order_store(tmp_path) -> OrderStore:
    return OrderStore(tmp_path / "orders.db")


@pytest.fixture
def session_store() -> SessionStore:
    return SessionStore()
