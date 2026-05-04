from __future__ import annotations

from pathlib import Path

import httpx

from ..config import STATE_DIR

COOKIE_PATH = STATE_DIR / "brainscape.cookie.txt"
BASE = "https://www.brainscape.com"


class BrainscapeAuthError(RuntimeError):
    pass


class BrainscapeClient:
    def __init__(self, cookie: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url=BASE,
            timeout=timeout,
            headers={
                "Cookie": cookie,
                "User-Agent": "flashcard-sync/0.1 (+https://github.com/Adenegar/flashcard-sync)",
                "Accept": "application/json",
            },
        )

    @classmethod
    def from_state_dir(cls, path: Path = COOKIE_PATH) -> "BrainscapeClient":
        if not path.exists():
            raise BrainscapeAuthError(
                f"No cookie at {path}. Capture one (see README) and place it there."
            )
        cookie = path.read_text().strip()
        if not cookie:
            raise BrainscapeAuthError(f"{path} is empty.")
        return cls(cookie)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BrainscapeClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def deck_preview(self, pack_id: str, deck_id: str) -> dict:
        """Fetch a deck's full card list via the undocumented preview endpoint."""
        r = self._client.get(f"/api/packs/{pack_id}/decks/{deck_id}/preview")
        if r.status_code in (401, 403):
            raise BrainscapeAuthError(
                f"Brainscape rejected the session cookie ({r.status_code}). "
                "Re-capture it via DevTools console: copy(document.cookie)."
            )
        r.raise_for_status()
        return r.json()
