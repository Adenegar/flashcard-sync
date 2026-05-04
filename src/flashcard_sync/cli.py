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


@auth.command("brainscape")
def auth_brainscape() -> None:
    """Capture a Brainscape Pro session cookie. (Phase 2)"""
    console.print("[yellow]Not implemented yet — lands in Phase 2.[/]")


@cli.command("add-deck")
def add_deck() -> None:
    """Interactively add a deck to sync.config.toml. (Phase 2)"""
    console.print("[yellow]Not implemented yet — lands in Phase 2.[/]")


@cli.command()
def pull() -> None:
    """Fetch current state from Brainscape and Anki into .sync-state/. (Phase 2)"""
    cfg = _load_config_or_exit()
    console.print(f"Loaded config with {len(cfg.deck)} deck(s).")
    console.print("[yellow]pull not implemented yet — lands in Phase 2.[/]")


@cli.command()
def diff() -> None:
    """Show pending changes per side without writing. (Phase 3+)"""
    console.print("[yellow]Not implemented yet — lands in Phase 3.[/]")


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
