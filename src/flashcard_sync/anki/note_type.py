"""Definition of the BrainscapeSync Anki note type and idempotent install."""
from __future__ import annotations

from .client import AnkiClient

MODEL_NAME = "BrainscapeSync"

FIELDS = [
    "SyncID",
    "BrainscapeCardId",
    "FrontPrompt",
    "FrontBody",
    "FrontClarifier",
    "FrontFootnote",
    "BackPrompt",
    "BackBody",
    "BackClarifier",
    "BackFootnote",
    "FrontHtml",
    "BackHtml",
]

CSS = """\
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 18px;
  text-align: left;
  color: #1a1a1a;
  background: #fff;
  padding: 1em;
}
.card .prompt { color: #666; font-size: 0.85em; margin-bottom: 0.5em; }
.card .body { font-size: 1.1em; margin-bottom: 0.5em; }
.card .clarifier { color: #444; font-style: italic; margin-top: 0.5em; }
.card .footnote { color: #777; font-size: 0.85em; margin-top: 0.75em;
                  border-top: 1px solid #eee; padding-top: 0.5em; }
hr#answer { margin: 1.25em 0; border: none; border-top: 2px solid #ddd; }
strong { color: #000; }
"""

FRONT_TEMPLATE = """\
{{#FrontPrompt}}<div class="prompt">{{FrontPrompt}}</div>{{/FrontPrompt}}
<div class="body">{{FrontHtml}}</div>
{{#FrontClarifier}}<div class="clarifier">{{FrontClarifier}}</div>{{/FrontClarifier}}
{{#FrontFootnote}}<div class="footnote">{{FrontFootnote}}</div>{{/FrontFootnote}}
"""

BACK_TEMPLATE = """\
{{FrontSide}}
<hr id="answer">
{{#BackPrompt}}<div class="prompt">{{BackPrompt}}</div>{{/BackPrompt}}
<div class="body">{{BackHtml}}</div>
{{#BackClarifier}}<div class="clarifier">{{BackClarifier}}</div>{{/BackClarifier}}
{{#BackFootnote}}<div class="footnote">{{BackFootnote}}</div>{{/BackFootnote}}
"""

TEMPLATES = [
    {"Name": "Card 1", "Front": FRONT_TEMPLATE, "Back": BACK_TEMPLATE},
]


def ensure_model(client: AnkiClient) -> None:
    """Create the BrainscapeSync note type if it doesn't already exist."""
    if MODEL_NAME in client.model_names():
        return
    client.create_model(MODEL_NAME, FIELDS, CSS, TEMPLATES)


def ensure_deck(client: AnkiClient, deck_name: str) -> None:
    client.create_deck(deck_name)  # idempotent in AnkiConnect
