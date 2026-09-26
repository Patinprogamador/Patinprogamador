def test_menu_loads_items_from_seed_file(menu):
    items = menu.all_items()
    assert len(items) > 0
    assert all(item.price > 0 for item in items)


def test_menu_find_returns_item_by_id(menu):
    item = menu.find("pizza_margherita_m")
    assert item is not None
    assert item.name == "Pizza Margherita (Média)"


def test_menu_find_returns_none_for_unknown_id(menu):
    assert menu.find("does_not_exist") is None


def test_menu_prompt_text_groups_by_category(menu):
    text = menu.as_prompt_text()
    assert "## Pizzas" in text
    assert "## Bebidas" in text
    assert "id=pizza_margherita_m" in text
