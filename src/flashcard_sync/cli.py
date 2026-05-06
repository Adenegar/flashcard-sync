from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from .config import CONFIG_PATH, CONFLICTS_DIR, DECKS_DIR, STATE_DIR, SyncConfig

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """Two-way sync between Brainscape and Anki."""


@cli.command()
def init() -> None:
    """Scaffold config + state directories in the current repo."""
    for d in (STATE_DIR, DECKS_DIR, CONFLICTS_DIR):
        d.mkdir(exist_ok=True)
    if not CONFIG_PATH.exists():
        example = Path("sync.config.toml.example")
        if example.exists():
            CONFIG_PATH.write_text(example.read_text())
            console.print(f"[green]Created {CONFIG_PATH}[/]. Edit it to list decks to sync.")
        else:
            console.print("[yellow]No example config found; create sync.config.toml manually.[/]")
    else:
        console.print(f"[blue]{CONFIG_PATH} already exists; leaving as-is.[/]")
    console.print("Run [bold]sync auth brainscape[/] next.")


@cli.group()
def auth() -> None:
    """Manage credentials for external services."""


_BROWSERS = ["chrome", "safari", "firefox", "edge", "brave", "chromium", "arc", "opera", "vivaldi"]


@auth.command("brainscape")
@click.option(
    "--browser",
    type=click.Choice(_BROWSERS),
    help="Browser whose cookie store to read. Required unless --curl-file is given.",
)
@click.option(
    "--curl-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Fallback: read cookie from a 'Copy as cURL' dump instead of the browser.",
)
def auth_brainscape(browser: str | None, curl_file: Path | None) -> None:
    """Pull the Brainscape session cookie straight from your browser."""
    if curl_file is not None:
        cookie = _cookie_from_curl(curl_file.read_text())
    else:
        if browser is None:
            console.print(
                "[red]Specify --browser to avoid prompting every Chromium-based browser's keychain.[/]\n"
                f"Choices: {', '.join(_BROWSERS)}"
            )
            raise SystemExit(2)
        cookie = _cookie_from_browser(browser)

    names = {p.strip().split("=", 1)[0] for p in cookie.split(";") if "=" in p}
    has_session = any("_Brainscape_session" in n for n in names)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "brainscape.cookie.txt"
    path.write_text(cookie)
    path.chmod(0o600)

    msg = f"Saved {len(names)} cookie(s) to {path}."
    if not has_session:
        console.print(f"[yellow]{msg} Warning: no _Brainscape_session cookie — auth may fail.[/]")
    else:
        console.print(f"[green]{msg}[/]")


def _cookie_from_browser(browser: str) -> str:
    try:
        import browser_cookie3 as bc3
    except ImportError:
        console.print("[red]browser-cookie3 not installed. Run `uv pip install -e .` to refresh deps.[/]")
        raise SystemExit(1)

    fn = getattr(bc3, browser, None)
    if fn is None:
        console.print(f"[red]browser-cookie3 has no loader for {browser!r}.[/]")
        raise SystemExit(1)
    try:
        jar = fn(domain_name="brainscape.com")
    except Exception as e:
        console.print(
            f"[red]Couldn't read {browser} cookies: {e}[/]\n"
            "On macOS Chromium-based browsers may prompt for Keychain access on the first run."
        )
        raise SystemExit(1)

    cookies = [c for c in jar if "brainscape.com" in (c.domain or "")]
    if not cookies:
        console.print(
            "[red]No brainscape.com cookies found. "
            "Sign in at https://www.brainscape.com first, then re-run.[/]"
        )
        raise SystemExit(1)
    return "; ".join(f"{c.name}={c.value}" for c in cookies)


def _cookie_from_curl(text: str) -> str:
    import re

    match = re.search(r"-H \$?'[Cc]ookie:\s*([^']+)'", text) or re.search(
        r"-b \$?'([^']+)'", text
    )
    if not match:
        console.print("[red]No Cookie header found in that cURL dump.[/]")
        raise SystemExit(1)
    return match.group(1).strip()


@cli.command("add-deck")
def add_deck() -> None:
    """Interactively add a deck to sync.config.toml. (Phase 2)"""
    console.print("[yellow]Not implemented yet — lands in Phase 2.[/]")


@cli.command()
@click.option("--deck", "deck_filter", default=None, help="Only pull this deck name.")
@click.option("--side", type=click.Choice(["both", "brainscape", "anki"]), default="both")
def pull(deck_filter: str | None, side: str) -> None:
    """Fetch current state from Brainscape and Anki into .sync-state/."""
    from .anki.client import AnkiClient
    from .brainscape.client import BrainscapeClient
    from .snapshot import snapshot_anki, snapshot_brainscape, write_snapshot

    cfg = _load_config_or_exit()
    decks = cfg.deck if deck_filter is None else [d for d in cfg.deck if d.name == deck_filter]
    if not decks:
        console.print(f"[red]No deck matching {deck_filter!r} in config.[/]")
        raise SystemExit(1)

    bs_client = BrainscapeClient.from_state_dir() if side in ("both", "brainscape") else None
    anki_client = AnkiClient(cfg.anki.connect_url) if side in ("both", "anki") else None

    try:
        for deck in decks:
            console.print(f"[bold]{deck.name}[/]")
            if bs_client is not None:
                snap = snapshot_brainscape(bs_client, deck)
                path = write_snapshot("brainscape", deck, snap)
                console.print(f"  brainscape: {snap['card_count']} cards → {path}")
            if anki_client is not None:
                snap = snapshot_anki(anki_client, deck)
                path = write_snapshot("anki", deck, snap)
                console.print(f"  anki:       {snap['card_count']} cards → {path}")
    finally:
        if bs_client is not None:
            bs_client.close()
        if anki_client is not None:
            anki_client.close()


@cli.command()
def diff() -> None:
    """Show pending changes per side without writing. (Phase 6)"""
    console.print("[yellow]Not implemented yet — lands in Phase 6.[/]")


@cli.command()
@click.option("--deck", "deck_filter", default=None, help="Only push this deck name.")
@click.option(
    "--to",
    "destination",
    type=click.Choice(["anki", "brainscape"]),
    default="anki",
    help="Push direction.",
)
@click.option("--dry-run", is_flag=True, help="Show what would happen without writing.")
def push(deck_filter: str | None, destination: str, dry_run: bool) -> None:
    """Push pending changes to a destination (phase 3: BS→Anki adds only)."""
    from .anki.client import AnkiClient
    from .brainscape.client import BrainscapeClient
    from .push_anki import push_brainscape_to_anki
    from .snapshot import snapshot_brainscape

    if destination == "brainscape":
        console.print("[yellow]Anki → Brainscape lands in Phase 5.[/]")
        return

    cfg = _load_config_or_exit()
    decks = cfg.deck if deck_filter is None else [d for d in cfg.deck if d.name == deck_filter]
    if not decks:
        console.print(f"[red]No deck matching {deck_filter!r} in config.[/]")
        raise SystemExit(1)

    with BrainscapeClient.from_state_dir() as bs, AnkiClient(cfg.anki.connect_url) as anki:
        for deck in decks:
            console.print(f"[bold]{deck.name}[/]")
            bs_snap = snapshot_brainscape(bs, deck)
            push_brainscape_to_anki(anki, deck, bs_snap, dry_run=dry_run)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Show planned writes without executing.")
def run(dry_run: bool) -> None:  # noqa: ARG001
    """Run a full two-way sync and commit on success. (Phase 6)"""
    console.print("[yellow]Not implemented yet — lands in Phase 6.[/]")


@cli.command()
@click.argument("conflict_id", required=False)
def resolve(conflict_id: str | None) -> None:  # noqa: ARG001
    """Interactively resolve a sync conflict. (Phase 6)"""
    console.print("[yellow]Not implemented yet — lands in Phase 6.[/]")


@cli.command()
def status() -> None:
    """Show last sync time, pending conflicts, deck health. (Phase 7)"""
    console.print("[yellow]Not implemented yet — lands in Phase 7.[/]")


def _load_config_or_exit() -> SyncConfig:
    if not CONFIG_PATH.exists():
        console.print(f"[red]No {CONFIG_PATH} found. Run `sync init` first.[/]")
        raise SystemExit(1)
    return SyncConfig.load(CONFIG_PATH)


if __name__ == "__main__":
    cli()
