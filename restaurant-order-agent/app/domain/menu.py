from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MenuItem:
    id: str
    name: str
    category: str
    description: str
    price: float


class Menu:
    def __init__(self, items: list[MenuItem]):
        self._items_by_id = {item.id: item for item in items}

    @classmethod
    def from_json_file(cls, path: Path) -> "Menu":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([MenuItem(**entry) for entry in raw])

    def find(self, item_id: str) -> MenuItem | None:
        return self._items_by_id.get(item_id)

    def all_items(self) -> list[MenuItem]:
        return list(self._items_by_id.values())

    def as_prompt_text(self) -> str:
        by_category: dict[str, list[MenuItem]] = {}
        for item in self._items_by_id.values():
            by_category.setdefault(item.category, []).append(item)

        lines: list[str] = []
        for category, items in by_category.items():
            lines.append(f"## {category}")
            for item in items:
                lines.append(
                    f"- id={item.id} | {item.name} — R$ {item.price:.2f} — {item.description}"
                )
        return "\n".join(lines)
