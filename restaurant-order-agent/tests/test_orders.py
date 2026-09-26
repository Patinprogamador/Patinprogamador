from app.domain.orders import OrderItem, OrderStatus


def test_create_and_get_order(order_store):
    items = [OrderItem(item_id="pizza_margherita_m", name="Pizza Margherita", unit_price=42.90, quantity=2)]
    order = order_store.create_order("5511999999999", items)

    assert order.id is not None
    assert order.status == OrderStatus.RECEIVED
    assert order.total() == 85.80

    fetched = order_store.get_order(order.id)
    assert fetched is not None
    assert fetched.customer_phone == "5511999999999"
    assert fetched.items == items


def test_latest_order_for_customer_returns_most_recent(order_store):
    items = [OrderItem(item_id="agua_mineral", name="Água", unit_price=4.0, quantity=1)]
    order_store.create_order("111", items)
    second = order_store.create_order("111", items)
    order_store.create_order("222", items)

    latest = order_store.latest_order_for_customer("111")
    assert latest is not None
    assert latest.id == second.id


def test_latest_order_for_unknown_customer_is_none(order_store):
    assert order_store.latest_order_for_customer("nobody") is None


def test_update_status(order_store):
    items = [OrderItem(item_id="agua_mineral", name="Água", unit_price=4.0, quantity=1)]
    order = order_store.create_order("111", items)

    updated = order_store.update_status(order.id, OrderStatus.OUT_FOR_DELIVERY)
    assert updated is True

    fetched = order_store.get_order(order.id)
    assert fetched.status == OrderStatus.OUT_FOR_DELIVERY


def test_update_status_unknown_order_returns_false(order_store):
    assert order_store.update_status(9999, OrderStatus.DELIVERED) is False
