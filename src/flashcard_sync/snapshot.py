"""Per-side snapshots stored under .sync-state/. Phase-2 output: lets us inspect
what each system currently shows without committing anything to git yet."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .anki.client import AnkiClient
from .brainscape.client import BrainscapeClient
from .canonical.schema import CardFace
from .config import DeckConfig, STATE_DIR


def _safe(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_")


def snapshot_brainscape(client: BrainscapeClient, deck: DeckConfig) -> dict[str, Any]:
    raw = client.deck_preview(deck.brainscape_pack_id, deck.brainscape_deck_id)
    cards = []
    for c in raw.get("cards", []):
        front = CardFace(
            prompt=c.get("qMdPrompt") or None,
            body=c.get("qMdBody") or c.get("question") or "",
            clarifier=c.get("qMdClarifier") or None,
            footnote=c.get("qMdFootnote") or None,
        )
        back = CardFace(
            prompt=c.get("aMdPrompt") or None,
            body=c.get("aMdBody") or c.get("answer") or "",
            clarifier=c.get("aMdClarifier") or None,
            footnote=c.get("aMdFootnote") or None,
        )
        cards.append({
            "brainscape_card_id": int(c["cardId"]),
            "front": front.model_dump(),
            "back": back.model_dump(),
            "updated_at": c.get("updatedAt"),
        })
    return {
        "deck_name": raw.get("deck", {}).get("name"),
        "pack_id": deck.brainscape_pack_id,
        "deck_id": deck.brainscape_deck_id,
        "card_count": len(cards),
        "cards": cards,
    }


def snapshot_anki(client: AnkiClient, deck: DeckConfig) -> dict[str, Any]:
    """Best-effort snapshot. We don't yet know which note fields map to which face;
    for phase 2 we just record a flat representation per note for inspection."""
    note_ids = client.find_notes(f'deck:"{deck.anki_deck}"')
    notes = client.notes_info(note_ids)
    cards = []
    for n in notes:
        fields = {k: v.get("value", "") for k, v in n.get("fields", {}).items()}
        # Heuristic: Front/Back if standard Basic; otherwise first two fields by order.
        if "Front" in fields and "Back" in fields:
            front_body, back_body = fields["Front"], fields["Back"]
        else:
            ordered = sorted(n.get("fields", {}).items(), key=lambda kv: kv[1].get("order", 0))
            front_body = ordered[0][1].get("value", "") if ordered else ""
            back_body = ordered[1][1].get("value", "") if len(ordered) > 1 else ""
        cards.append({
            "anki_note_id": int(n["noteId"]),
            "model": n.get("modelName"),
            "tags": list(n.get("tags", [])),
            "fields": fields,
            "front_body": front_body,
            "back_body": back_body,
        })
    return {
        "deck_name": deck.anki_deck,
        "card_count": len(cards),
        "cards": cards,
    }


def write_snapshot(side: str, deck: DeckConfig, payload: dict[str, Any]) -> Path:
    out_dir = STATE_DIR / side
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_safe(deck.name)}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return path
