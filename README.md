# flashcard-sync

Sync individual decks between Brainscape (Pro) and Anki. Card content stays on this machine; only code is in the GitHub repo.

## Setup

Install and scaffold the local config + state directories:

```bash
git clone https://github.com/Adenegar/flashcard-sync.git
cd flashcard-sync
uv venv && uv pip install -e ".[dev]"
.venv/bin/sync init
```

### Authenticate to Brainscape

Brainscape has no public API, so this tool reuses the session cookie from a browser you've already signed in with. Sign in to https://www.brainscape.com in your browser of choice and leave the tab open, then run:

```bash
.venv/bin/sync auth brainscape --browser firefox
```

`--browser` is required — picking one avoids prompting every installed browser's keychain. Supported: `chrome`, `safari`, `firefox`, `edge`, `brave`, `chromium`, `arc`, `opera`, `vivaldi`.

A few notes per browser:

- **Chrome / Edge / Brave / Arc / other Chromium-based:** quit the browser first — it holds an exclusive lock on its cookie DB while running. macOS will prompt for Keychain access on the first run; click **Always Allow** so future runs are silent.
- **Safari and Firefox:** no Keychain prompt and no need to quit the browser; cookies are read straight from disk.

The cookie is saved to a state directory under your home folder (chmod 600) and expires every couple of weeks. When it does, a Brainscape API call returns 403 — visit brainscape.com in your browser to refresh the session, then re-run the same `sync auth brainscape --browser X` command.

If the browser route fails (locked profile, unusual setup, etc.), fall back to a manual capture: in DevTools → Network, right-click any brainscape.com request → **Copy as cURL**, save to a file, then run `sync auth brainscape --curl-file path/to/dump.txt`.

### Configure decks

Edit `sync.config.toml` to add the decks you want to sync. Each deck needs its own `[[deck]]` table (TOML's array-of-tables syntax). Find the IDs in the Brainscape URL:

```
brainscape.com/flashcards/<slug>-<DECK_ID>/packs/<PACK_ID>
```

## Running a sync

Anki desktop must be running while these commands execute — AnkiConnect is an in-process HTTP server inside Anki, so the desktop app needs to be open and unlocked.

Snapshot both sides into `.sync-state/` without writing anything. Useful for inspecting what's currently on each side:

```bash
sync pull
sync pull --side brainscape           # only one side
sync pull --side anki
sync pull --deck "Name"               # scope to one deck
```

Add cards that exist on Brainscape but not yet in Anki. Idempotent — re-running won't duplicate cards:

```bash
sync push --to anki --dry-run         # preview the plan first
sync push --to anki
sync push --to anki --deck "Name"     # scope to one deck
```

After a successful `sync push`, click **Sync** in Anki desktop to propagate to AnkiWeb and your other devices. The tool only writes to your local Anki collection.

Current scope: BS → Anki **adds only**. Edits, deletes, and the Anki → Brainscape direction aren't implemented yet.

## Data

Card content is written to `decks/<name>/cards.json`, which is gitignored. If that file is lost, the next `sync push --to anki` rebuilds it from the `BrainscapeCardId` field on existing Anki notes.
