from pytest_httpx import HTTPXMock

from flashcard_sync.brainscape.client import BrainscapeClient
from flashcard_sync.config import DeckConfig
from flashcard_sync.snapshot import snapshot_brainscape

SAMPLE = {
    "deck": {"name": "Test Deck"},
    "cards": [
        {
            "cardId": 111,
            "qMdPrompt": None,
            "qMdBody": "What is 2+2?",
            "qMdClarifier": None,
            "qMdFootnote": None,
            "aMdPrompt": None,
            "aMdBody": "4",
            "aMdClarifier": "basic arithmetic",
            "aMdFootnote": None,
            "question": "What is 2+2?",
            "answer": "4\n\nbasic arithmetic",
            "updatedAt": "2026-05-04T00:00:00Z",
        },
        {
            "cardId": 222,
            "qMdBody": "Capital of France?",
            "aMdBody": "Paris",
            "question": "Capital of France?",
            "answer": "Paris",
            "updatedAt": "2026-05-04T00:00:00Z",
        },
    ],
}


def test_snapshot_brainscape_extracts_structured_faces(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://www.brainscape.com/api/packs/9/decks/8/preview",
        json=SAMPLE,
    )
    deck = DeckConfig(
        name="t",
        brainscape_pack_id="9",
        brainscape_deck_id="8",
        anki_deck="X",
    )
    with BrainscapeClient(cookie="x=y") as c:
        snap = snapshot_brainscape(c, deck)

    assert snap["card_count"] == 2
    assert snap["deck_name"] == "Test Deck"
    first = snap["cards"][0]
    assert first["brainscape_card_id"] == 111
    assert first["front"]["body"] == "What is 2+2?"
    assert first["back"]["body"] == "4"
    assert first["back"]["clarifier"] == "basic arithmetic"
    assert first["back"]["footnote"] is None
