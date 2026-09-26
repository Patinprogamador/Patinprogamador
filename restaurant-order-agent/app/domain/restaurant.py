from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RestaurantInfo:
    name: str
    address: str
    phone: str


@dataclass(frozen=True)
class FaqEntry:
    question: str
    answer: str


def load_faq(path: Path) -> list[FaqEntry]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [FaqEntry(**entry) for entry in raw]


def faq_as_prompt_text(faq: list[FaqEntry]) -> str:
    return "\n".join(f"P: {entry.question}\nR: {entry.answer}" for entry in faq)
