from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


Direction = Literal["two-way", "bs-to-anki", "anki-to-bs"]


class AnkiConfig(BaseModel):
    connect_url: str = "http://127.0.0.1:8765"


class BrainscapeConfig(BaseModel):
    pass


class DeckConfig(BaseModel):
    name: str
    brainscape_pack_id: str
    brainscape_deck_id: str
    anki_deck: str
    direction: Direction = "two-way"

    @field_validator("name")
    @classmethod
    def _name_safe(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("deck name must not be empty")
        if any(c in v for c in "/\\"):
            raise ValueError("deck name must not contain slashes")
        return v


class SyncConfig(BaseModel):
    anki: AnkiConfig = Field(default_factory=AnkiConfig)
    brainscape: BrainscapeConfig = Field(default_factory=BrainscapeConfig)
    deck: list[DeckConfig] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "SyncConfig":
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)


CONFIG_PATH = Path("sync.config.toml")
STATE_DIR = Path(".sync-state")
DECKS_DIR = Path("decks")
CONFLICTS_DIR = Path("conflicts")
