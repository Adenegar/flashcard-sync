# flashcard-sync

Sync individual decks between Brainscape (Pro) and Anki. Card content stays on this machine; only code is in the GitHub repo.

## Setup

```bash
git clone https://github.com/Adenegar/flashcard-sync.git
cd flashcard-sync
uv venv && uv pip install -e ".[dev]"
.venv/bin/sync init
.venv/bin/sync auth brainscape   # follow the prompt
```

Edit `sync.config.toml` to add a deck. Find the IDs in the Brainscape URL:

```
brainscape.com/flashcards/<slug>-<DECK_ID>/packs/<PACK_ID>
```

Each deck needs its own `[[deck]]` header — TOML's array-of-tables syntax.

## Commands

Anki desktop must be open (AnkiConnect runs in-process).

```
sync pull                            # snapshot both sides into .sync-state/
sync push --to anki [--dry-run]      # add new BS cards to Anki (idempotent)
sync push --deck "Name"              # limit to one deck
sync auth brainscape                 # recapture cookie when expired
```

## Gotchas

- The Brainscape cookie expires every couple of weeks. A 403 means run `sync auth brainscape` again.
- After `sync push`, click **Sync** in Anki desktop to reach AnkiWeb / other devices.
- BS → Anki currently does **adds only**. Edits and deletes (both directions) are not yet implemented.

## Data

Card content is written to `decks/<name>/cards.json`, which is gitignored. If that file is lost, the next `sync push --to anki` rebuilds it from the `BrainscapeCardId` field on existing Anki notes.
