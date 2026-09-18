# Neko Metadata Getter

Fills in missing metadata (title, artist, album, album artist, genre,
year, track number, cover art) on downloaded music files by looking
them up on [MusicBrainz](https://musicbrainz.org), with
[Discogs](https://www.discogs.com) as an optional fallback for
anything MusicBrainz didn't have.

It works on `.mp3`, `.m4a`, `.mp4` (audio), and `.flac` files -- format
is detected from the file's actual contents, not its extension, so a
mislabeled `.mp4` that's really an `.m4a` is handled correctly either
way.


## Setup

1. Install [Python 3.10+](https://www.python.org/downloads/) if you
   don't have it (make sure to check "Add python.exe to PATH" during
   install on Windows).
2. Download and unzip the files then open terminal in that unzipped folder
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. **(Optional)** Enable the Discogs fallback by getting a free
   personal access token from
   [discogs.com/settings/developers](https://www.discogs.com/settings/developers),
   then setting it as an environment variable:
   ```
   # macOS/Linux
   export DISCOGS_TOKEN="your_token_here"

   # Windows (PowerShell) -- open a new terminal afterward
   setx DISCOGS_TOKEN "your_token_here"
   ```
   Without a token, the script just uses MusicBrainz.

## Usage

**Single file** (always shows you a table of proposed changes to
confirm, edit, or reject before writing):
```
python fix_metadata.py "/path/to/song.mp3"
```

**Whole folder** (loops through every supported audio file inside;
confident MusicBrainz matches are tagged automatically, anything
uncertain still stops and asks you):
```
python fix_metadata.py "/path/to/folder"
```

At the end of a folder run you'll get a summary table showing what
happened to every file (`auto-tagged`, `confirmed`, `skipped`,
`no match`, or `error`).

