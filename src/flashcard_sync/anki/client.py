from __future__ import annotations

from typing import Any

import httpx


class AnkiConnectError(RuntimeError):
    pass


class AnkiClient:
    """Thin wrapper around AnkiConnect's JSON-RPC-ish HTTP API."""

    def __init__(self, url: str = "http://127.0.0.1:8765", *, timeout: float = 30.0) -> None:
        self._client = httpx.Client(base_url=url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AnkiClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _invoke(self, action: str, **params: Any) -> Any:
        try:
            r = self._client.post("/", json={"action": action, "version": 6, "params": params})
        except httpx.ConnectError as e:
            raise AnkiConnectError(
                "Could not reach AnkiConnect. Is Anki desktop open with the AnkiConnect "
                "add-on installed (code 2055492159)?"
            ) from e
        r.raise_for_status()
        body = r.json()
        if body.get("error"):
            raise AnkiConnectError(f"AnkiConnect error on {action}: {body['error']}")
        return body.get("result")

    def version(self) -> int:
        return int(self._invoke("version"))

    def deck_names(self) -> list[str]:
        return list(self._invoke("deckNames"))

    def find_notes(self, query: str) -> list[int]:
        return list(self._invoke("findNotes", query=query))

    def notes_info(self, note_ids: list[int]) -> list[dict]:
        if not note_ids:
            return []
        return list(self._invoke("notesInfo", notes=note_ids))

    def media_file(self, filename: str) -> str | None:
        """Return base64-encoded media content, or None if missing."""
        try:
            return self._invoke("retrieveMediaFile", filename=filename)
        except AnkiConnectError:
            return None
