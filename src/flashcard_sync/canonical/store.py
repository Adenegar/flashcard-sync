"""Read/write the committed canonical cards.json per deck."""
from __future__ import annotations

import json
from pathlib import Path

from ..config import DECKS_DIR
from .schema import Card, Deck


def _safe(name: str) -> str:
    return name.replace("/", "_")


def deck_path(deck_name: str) -> Path:
    return DECKS_DIR / _safe(deck_name) / "cards.json"


def load(deck_name: str) -> Deck | None:
    p = deck_path(deck_name)
    if not p.exists():
        return None
    return Deck.model_validate_json(p.read_text())


def save(deck: Deck) -> Path:
    p = deck_path(deck.name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(deck.model_dump_json(indent=2, exclude_none=False))
    return p


def index_by_brainscape_id(deck: Deck) -> dict[int, Card]:
    return {c.brainscape_card_id: c for c in deck.cards if c.brainscape_card_id is not None}
