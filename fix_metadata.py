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

console.print(table)

choice = Prompt.ask(
    "\n[bold]Write these tags?₍^. .^₎⟆[/bold]", choices=["y", "n", "e"], default="y"
    

    




    