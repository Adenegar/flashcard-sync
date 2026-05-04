from __future__ import annotations

import hashlib
import re
from pathlib import Path

from pydantic import BaseModel, Field


class Media(BaseModel):
    sha256: str
    filename: str
    mime: str


class Card(BaseModel):
    sync_id: str
    front: str
    back: str
    media: list[Media] = Field(default_factory=list)

    brainscape_id: str | None = None
    anki_note_id: int | None = None

    last_seen_brainscape_hash: str | None = None
    last_seen_anki_hash: str | None = None

    def content_hash(self) -> str:
        normalized = _normalize(self.front) + "\x1f" + _normalize(self.back)
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
    """Normalize whitespace and trim. Preserve case and content otherwise."""
    return _WS.sub(" ", text).strip()
