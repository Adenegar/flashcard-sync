from __future__ import annotations

import hashlib
import re
from pathlib import Path

from pydantic import BaseModel, Field


class Media(BaseModel):
    sha256: str
    filename: str
    mime: str


class CardFace(BaseModel):
    """One side of a card. Brainscape splits markdown into 4 named components;
    Anki cards just populate `body` unless they came from our BrainscapeSync note type."""
    prompt: str | None = None
    body: str = ""
    clarifier: str | None = None
    footnote: str | None = None

    def to_text(self) -> str:
        parts = [p for p in (self.prompt, self.body, self.clarifier, self.footnote) if p]
        return "\n\n".join(parts)


class Card(BaseModel):
    sync_id: str
    front: CardFace
    back: CardFace
    media: list[Media] = Field(default_factory=list)

    brainscape_card_id: int | None = None
    anki_note_id: int | None = None

    last_seen_brainscape_hash: str | None = None
    last_seen_anki_hash: str | None = None

    def content_hash(self) -> str:
        normalized = _normalize(self.front.to_text()) + "\x1f" + _normalize(self.back.to_text())
        for m in sorted(self.media, key=lambda x: x.sha256):
            normalized += "\x1f" + m.sha256
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class Deck(BaseModel):
    name: str
    brainscape_pack_id: str
    brainscape_deck_id: str
    anki_deck: str
    cards: list[Card] = Field(default_factory=list)

    def cards_path(self, root: Path) -> Path:
        return root / self.name / "cards.json"

    def media_dir(self, root: Path) -> Path:
        return root / self.name / "media"


_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", text).strip()
