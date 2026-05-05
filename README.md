# flashcard-sync

Two-way sync between [Brainscape](https://www.brainscape.com) and [Anki](https://apps.ankiweb.net/), one deck at a time. Card content lives only on your machine; this repo never commits it.

## Status

Working today:

- ✅ Pull from Brainscape (any deck you can see in your Pro account)
- ✅ Pull from Anki (via AnkiConnect)
- ✅ Push **new** Brainscape cards into Anki (BS → Anki adds)

Not built yet:

- ⏳ Updates and deletes from BS → Anki
- ⏳ Anki → Brainscape (additions via bulk-import; edits/deletes via manual checklist)
- ⏳ Two-way conflict resolution

## Prerequisites

- macOS (these instructions; Linux works the same)
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (`brew install uv`)
- Anki desktop with the **AnkiConnect** add-on (paste code `2055492159` into Tools → Add-ons → Get Add-ons, then restart Anki)
- A Brainscape Pro account

## One-time setup

```bash
git clone https://github.com/Adenegar/flashcard-sync.git
cd flashcard-sync
uv venv
uv pip install -e ".[dev]"
.venv/bin/sync init
```

`sync init` creates `sync.config.toml` (your deck list — gitignored) and the `.sync-state/` directory.

### Capture your Brainscape session cookie

The Brainscape API requires the session cookies your browser uses. We grab them once via DevTools.

1. Open `https://www.brainscape.com` in Chrome and sign in.
2. Open DevTools (`Cmd+Option+I`) → **Network** tab.
3. Check **Preserve log**. Filter by **Doc**.
4. Hard-reload (`Cmd+Shift+R`). You'll see rows for the page document.
5. Right-click any `brainscape.com` row → **Copy** → **Copy as cURL**.
6. Save it locally:

   ```bash
   pbpaste > .sync-state/brainscape.curl.txt && chmod 600 .sync-state/brainscape.curl.txt
   ```

7. Extract the Cookie header from the curl into the cookie file:

   ```bash
   .venv/bin/python -c "
   import re, pathlib
   text = pathlib.Path('.sync-state/brainscape.curl.txt').read_text()
   m = re.search(r\"-H \\\$?'[Cc]ookie:\\s*([^']+)'\", text) or re.search(r\"-b \\\$?'([^']+)'\", text)
   pathlib.Path('.sync-state/brainscape.cookie.txt').write_text(m.group(1))
   "
   chmod 600 .sync-state/brainscape.cookie.txt
   rm .sync-state/brainscape.curl.txt
   ```

The cookie expires periodically (weeks, typically). When `sync` returns 403, repeat the steps above.

## Adding a deck to sync

Find the Brainscape deck URL: navigate into a single deck and the URL looks like:

```
https://www.brainscape.com/flashcards/<slug>-<deckId>/packs/<packId>
                                              ↑              ↑
                                          deck_id        pack_id
```

Edit `sync.config.toml`:

```toml
[anki]
connect_url = "http://127.0.0.1:8765"

[[deck]]
name = "Mobile Devices"            # any label you'll recognize
brainscape_pack_id = "23636801"
brainscape_deck_id = "17779716"
anki_deck = "CompTIA A+::Mobile Devices"   # auto-created if missing
direction = "two-way"              # one of: two-way, bs-to-anki, anki-to-bs
```

Add as many `[[deck]]` blocks as you like.

## Daily commands

Open Anki desktop first (AnkiConnect needs it running).

```bash
# See what's currently on each side, no writes:
.venv/bin/sync pull

# Preview what a BS → Anki push would do:
.venv/bin/sync push --to anki --dry-run

# Actually do it:
.venv/bin/sync push --to anki

# Limit to one deck:
.venv/bin/sync push --to anki --deck "Mobile Devices"
```

After running `sync push`, open Anki and click **Sync** to push to AnkiWeb so the cards reach your other devices.

## Where things live

| Path | What | Tracked by git? |
|---|---|---|
| `sync.config.toml` | Your deck list | No (private to you) |
| `.sync-state/brainscape.cookie.txt` | BS session cookie | No |
| `.sync-state/{brainscape,anki}/<deck>.json` | Per-side snapshots from `sync pull` | No |
| `decks/<name>/cards.json` | Canonical state with `sync_id` ↔ `brainscape_card_id` ↔ `anki_note_id` mapping | **No — gitignored. Card content is private.** |
| `src/flashcard_sync/` | Code | Yes |

## How identity matching works

Each card gets a stable `sync_id` (UUID) minted on first sight. This is stored:

- **In Anki** — as the `SyncID` field on the `BrainscapeSync` note type, plus a `bsync:<uuid>` tag.
- **In Brainscape** — implicitly via the native `cardId`, which we keep in the `BrainscapeCardId` Anki field.

If `decks/<name>/cards.json` ever goes missing, the next `sync push --to anki` rebuilds it by reading those fields back from Anki.

## Troubleshooting

- **`Could not reach AnkiConnect`** — Anki desktop isn't open, or the add-on isn't installed.
- **`Brainscape rejected the session cookie (403)`** — recapture the cookie (see setup section).
- **A card you edited in Brainscape didn't update in Anki** — expected; updates aren't built yet (status section).
- **Cards in Anki show literal `**asterisks**`** — Brainscape stores markdown, and the Anki card template currently renders the structured fields as plain text. Proper markdown→HTML rendering is on the polish list.

## Running tests

```bash
.venv/bin/python -m pytest -q
```
