from pathlib import Path

import pytest

from flashcard_sync.config import SyncConfig


def test_loads_example_config(tmp_path: Path) -> None:
    src = Path("sync.config.toml.example")
    target = tmp_path / "sync.config.toml"
    target.write_text(src.read_text())
    cfg = SyncConfig.load(target)
    assert len(cfg.deck) == 1
    assert cfg.deck[0].direction == "two-way"
    assert cfg.anki.connect_url.startswith("http")


def test_rejects_slash_in_deck_name(tmp_path: Path) -> None:
    p = tmp_path / "c.toml"
    p.write_text(
        '[[deck]]\nname="bad/name"\nbrainscape_pack_id="1"\n'
        'brainscape_deck_id="2"\nanki_deck="X"\n'
    )
    with pytest.raises(ValueError):
        SyncConfig.load(p)
