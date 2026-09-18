import os 
import sys
from webbrowser import get

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "The 'rich' library is required to run this script. Please install it using 'pip install rich' and try again."
    ) from error

from sources.musicbrainz import (
    search_musicbrainz, is_confident_match, extract_metadata, get_cover_art
)
from sources.discogs import fill_missing_fields
from tagging import (
    detect_format, read_existing_tags, guess_from_filename, write_tags,
    FIELDS, AUDIO_EXTENSIONS
)

console = Console()
DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN")


def confirm_changes(existing, proposed):
    table = Table(title="Proposed Metadata", show_lines=False, header_style="bold magenta")
    table.add_column("Field", style="bold cyan")
    table.add_column("Current", style="white")
    table.add_column("Proposed", style="bold green")

    final = {}
    for field in FIELDS:
        old = str(existing.get(field, "") or "(empty)")
        new = str(proposed.get(field, "") or "(not found)")
        table.add_row(field, old, new)
        final[field] = proposed.get(field) or existing.get(field, "")

    console.print(table)


    choice = Prompt.ask(
    "\n[bold]Write these tags?₍^. .^₎⟆[/bold]", choices=["y", "n", "e"], default="y"

    )
    if choice == "n":
        return None
    if choice == "e":
        for field in FIELDS:
            val = Prompt.ask(f" [cyan]{field}[/cyan]", default=final[field])
            final[field] = val
    return final


def process_file(path, auto_mode=False):
    filename = os.path.basename(path)
    console.print(Panel(filename, title="Neko Metadata Getter", style="cyan"))

    audio = detect_format(path)
    console.print(f"Detected format: [bold]{type(audio).__name__}[/bold]")

    existing = read_existing_tags(path)
    artist_hint = existing.get("artist", "")
    title_hint = existing.get("title", "")
    if not (artist_hint and title_hint):
        fname_artist, fname_title = guess_from_filename(path)
        artist_hint = artist_hint or fname_artist
        title_hint = title_hint or fname_artist

    with console.status(f"[bold green]searching MusicBrainz for {artist_hint} - {title_hint}..."):
        recording = search_musicbrainz(artist_hint, title_hint)

    if not recording:
        console.print("[bold red]No match found (╥﹏╥).[/bold red] Try renaming the file to 'Artist - Title.ext' and run again.")
        return "no match"

    proposed = extract_metadata(recording)

    if DISCOGS_TOKEN:
        with console.status("[bold green]Checking Discogs for missing fields...⚞^. .^⚟"):
            proposed = fill_missing_fields(proposed, artist_hint, title_hint, DISCOGS_TOKEN)

        with console.status("[bold green]Fetching cover art...(─‿‿─)"):
            cover_bytes = get_cover_art(proposed.get("release_mbid"))

        if cover_bytes:
            console.print("[green]Cover art found!(＾▽＾)[/green]")
        else:
            console.print("[yellow]No cover art found on Cover Art Archive(╥﹏╥)[/yellow]")

        if auto_mode and is_confident_match(recording, artist_hint):
            final = {field: proposed.get(field) or existing.get(field, "") for field in FIELDS}
            write_tags(path, audio, final, cover_bytes)
            console.print("[bold green]Auto-tagged (confident match).[/bold green]")
            return "auto-tagged"

    if auto_mode:
        console.print("[yellow]Low-confidence match -- needs your review.[/yellow]")

    final = confirm_changes(existing, proposed)
    if final is None:
        console.print("[yellow]Cancelled -- no changes made╮(￣_￣)╭[/yellow]")
        return "skipped"

    write_tags(path, audio, final, cover_bytes)
    console.print(f"\n[bold green]Tags written successfully! ヽ(•‿•)ノ[/bold green] Tags written to: {path}")
    console.print("[bold cyan]Metadata Summary:[/bold cyan]")
    return "confirmed"


def run_batch(folder):
    files = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(AUDIO_EXTENSIONS) and os.path.isfile(os.path.join(folder, f))
    )
    if not files:
        console.print("[yellow]No supported audio files found in that folder.[/yellow]")
        return
 
    results = {}
    for filename in files:
        path = os.path.join(folder, filename)
        try:
            results[filename] = process_file(path, auto_mode=True)
        except Exception as e:
            console.print(f"[bold red]Error processing {filename}: {e}[/bold red]")
            results[filename] = "error"
        console.print()
 
    summary = Table(title="Batch Summary", header_style="bold magenta")
    summary.add_column("File")
    summary.add_column("Result")
    colors = {
        "auto-tagged": "green", "confirmed": "green", "edited": "green",
        "skipped": "yellow", "no match": "red", "error": "red",
    }
    for filename, status in results.items():
        color = colors.get(status, "white")
        summary.add_row(filename, f"[{color}]{status}[/{color}]")
    console.print(summary)
 
 
def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red] python fix_metadata.py <file_or_folder_path>")
        sys.exit(1)
 
    path = sys.argv[1]
 
    if os.path.isdir(path):
        run_batch(path)
    elif os.path.isfile(path):
        process_file(path, auto_mode=False)
    else:
        console.print("[bold red]Path not found.[/bold red]")
        sys.exit(1)
 
 
if __name__ == "__main__":
    main()