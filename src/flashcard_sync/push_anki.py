"""Push Brainscape state into Anki.

For phase 3 this is BS → Anki only; updates and deletes are minimal here.
The full diff/conflict path lands in phase 6.
"""
from __future__ import annotations

import uuid
from typing import Any

from rich.console import Console

from .anki.client import AnkiClient
from .anki.note_type import MODEL_NAME, ensure_deck, ensure_model
from .canonical import store
from .canonical.schema import Card, CardFace, Deck
from .config import DeckConfig

console = Console()

BS_TAG_PREFIX = "bs-card:"
SYNC_TAG_PREFIX = "bsync:"


def _existing_anki_notes_by_bs_id(client: AnkiClient, deck_name: str) -> dict[int, dict]:
    note_ids = client.find_notes(f'deck:"{deck_name}" "note:{MODEL_NAME}"')
    notes = client.notes_info(note_ids)
    out: dict[int, dict] = {}
    for n in notes:
        bs_id_field = n.get("fields", {}).get("BrainscapeCardId", {}).get("value", "")
        if bs_id_field.isdigit():
            out[int(bs_id_field)] = n
    return out


def _build_anki_note(deck_name: str, sync_id: str, bs_card: dict[str, Any]) -> dict[str, Any]:
    front = bs_card["front"]
    back = bs_card["back"]
    return {
        "deckName": deck_name,
        "modelName": MODEL_NAME,
        "fields": {
            "SyncID": sync_id,
            "BrainscapeCardId": str(bs_card["brainscape_card_id"]),
            "FrontPrompt": front.get("prompt") or "",
            "FrontBody": front.get("body") or "",
            "FrontClarifier": front.get("clarifier") or "",
            "FrontFootnote": front.get("footnote") or "",
            "BackPrompt": back.get("prompt") or "",
            "BackBody": back.get("body") or "",
            "BackClarifier": back.get("clarifier") or "",
            "BackFootnote": back.get("footnote") or "",
            "FrontHtml": bs_card.get("front_html") or front.get("body") or "",
            "BackHtml": bs_card.get("back_html") or back.get("body") or "",
        },
        "tags": [
            f"{BS_TAG_PREFIX}{bs_card['brainscape_card_id']}",
            f"{SYNC_TAG_PREFIX}{sync_id}",
        ],
        "options": {"allowDuplicate": True},
    }


def push_brainscape_to_anki(
    client: AnkiClient,
    deck_cfg: DeckConfig,
    bs_snapshot: dict[str, Any],
    *,
    dry_run: bool = False,
) -> Deck:
    """Idempotently push a Brainscape snapshot into Anki and update canonical state.

    On first run: creates note type + deck, adds all cards, writes cards.json.
    On subsequent runs: adds cards new to BS, leaves existing alone (full
    update/delete diff lands in phase 6).
    """
    if not dry_run:
        ensure_model(client)
        ensure_deck(client, deck_cfg.anki_deck)

    existing = (
        _existing_anki_notes_by_bs_id(client, deck_cfg.anki_deck)
        if MODEL_NAME in client.model_names()
        else {}
    )
    canonical = store.load(deck_cfg.name) or Deck(
        name=deck_cfg.name,
        brainscape_pack_id=deck_cfg.brainscape_pack_id,
        brainscape_deck_id=deck_cfg.brainscape_deck_id,
        anki_deck=deck_cfg.anki_deck,
    )
    canonical_by_bs = {c.brainscape_card_id: c for c in canonical.cards if c.brainscape_card_id}

    # Rebuild canonical entries for cards that exist in Anki but not in the local
    # canonical store (e.g. after deleting decks/ to scrub it from git history).
    rebuilt = 0
    bs_by_id = {bsc["brainscape_card_id"]: bsc for bsc in bs_snapshot["cards"]}
    for bs_id, note in existing.items():
        if bs_id in canonical_by_bs:
            continue
        bs_card = bs_by_id.get(bs_id)
        if bs_card is None:
            continue  # in Anki but not in BS anymore — leave for delete pass in phase 6
        sync_id = note.get("fields", {}).get("SyncID", {}).get("value") or str(uuid.uuid4())
        card = Card(
            sync_id=sync_id,
            front=CardFace(**bs_card["front"]),
            back=CardFace(**bs_card["back"]),
            brainscape_card_id=bs_id,
            anki_note_id=int(note["noteId"]),
        )
        h = card.content_hash()
        card.last_seen_brainscape_hash = h
        card.last_seen_anki_hash = h
        canonical.cards.append(card)
        canonical_by_bs[bs_id] = card
        rebuilt += 1
    if rebuilt:
        store.save(canonical)
        console.print(f"  [dim]rebuilt {rebuilt} canonical entr{'y' if rebuilt == 1 else 'ies'} from Anki[/]")

    to_add: list[tuple[str, dict[str, Any]]] = []  # (sync_id, bs_card)
    for bs_card in bs_snapshot["cards"]:
        bs_id = bs_card["brainscape_card_id"]
        if bs_id in existing or bs_id in canonical_by_bs:
            continue
        sync_id = str(uuid.uuid4())
        to_add.append((sync_id, bs_card))

    if not to_add:
        console.print("  [dim]no new cards to add[/]")
        return canonical

    if dry_run:
        console.print(f"  [cyan]dry-run: would add {len(to_add)} card(s)[/]")
        for _, bsc in to_add[:5]:
            preview = (bsc["front"].get("body") or "")[:80]
            console.print(f"    + bs_id={bsc['brainscape_card_id']}  {preview}")
        if len(to_add) > 5:
            console.print(f"    … and {len(to_add) - 5} more")
        return canonical

    notes_payload = [_build_anki_note(deck_cfg.anki_deck, sid, bsc) for sid, bsc in to_add]
    note_ids = client.add_notes(notes_payload)

    added = 0
    failed = 0
    for (sync_id, bs_card), note_id in zip(to_add, note_ids):
        if note_id is None:
            failed += 1
            console.print(
                f"  [red]failed to add card bs_id={bs_card['brainscape_card_id']}[/]"
            )
            continue
        front = CardFace(**bs_card["front"])
        back = CardFace(**bs_card["back"])
        card = Card(
            sync_id=sync_id,
            front=front,
            back=back,
            brainscape_card_id=bs_card["brainscape_card_id"],
            anki_note_id=note_id,
        )
        h = card.content_hash()
        card.last_seen_brainscape_hash = h
        card.last_seen_anki_hash = h
        canonical.cards.append(card)
        added += 1

    store.save(canonical)
    console.print(f"  [green]added {added}[/]" + (f", [red]{failed} failed[/]" if failed else ""))
    return canonical
