try:
    import musicbrainzngs as mb
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "The 'musicbrainzngs' package is required. Install it with "
        "'python -m pip install musicbrainzngs'."
    ) from error

import requests

mb.set_useragent("neko-metadata-getter", "1.0", "https://github.com/Nekologyy")


def search_musicbrainz(artist_hint, title_hint):
    query_parts = []
    if title_hint:
        query_parts.append(f'recording:"{title_hint}"')
    if artist_hint:
        query_parts.append(f'artist:"{artist_hint}"')
    query = " AND ".join(query_parts) if query_parts else title_hint

    results = mb.search_recordings(query=query, limit=5)
    recordings = results.get("recording-list", [])
    if not recordings:
        return None

   
    for rec in recordings:
        if rec.get("release-list"):
            return rec
    return recordings[0]


def is_confident_match(recording, artist_hint):
    
    try:
        score = int(recording.get("ext:score", 0))
    except (TypeError, ValueError):
        score = 0
    if score < 90:
        return False
    if artist_hint:
        credited = (
            recording["artist-credit"][0]["artist"]["name"]
            if recording.get("artist-credit") else ""
        )
        if credited.strip().lower() != artist_hint.strip().lower():
            return False
    return True


def extract_metadata(recording):
    title = recording.get("title", "")
    artist = (
        recording.get("artist-credit")[0]["artist"]["name"]
        if recording.get("artist-credit") else ""
    )

    album = ""
    albumartist = artist
    year = ""
    tracknumber = ""
    release_mbid = None

    releases = recording.get("release-list", [])
    if releases:
        release = releases[0]
        album = release.get("title", "")
        release_mbid = release.get("id")
        date = release.get("date", "")
        year = date[:4] if date else ""
        if release.get("artist-credit"):
            albumartist = release["artist-credit"][0]["artist"]["name"]
        for medium in release.get("medium-list", []):
            for track in medium.get("track-list", []):
                if track.get("recording", {}).get("id") == recording.get("id"):
                    tracknumber = track.get("number", "")

    # MusicBrainz has no clean per-track genre field; fall back to the
    # recording's top community tag, if any (often empty -- normal).
    genre = ""
    tag_list = recording.get("tag-list", [])
    if tag_list:
        genre = sorted(tag_list, key=lambda t: -int(t.get("count", 0)))[0]["name"]

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "albumartist": albumartist,
        "genre": genre,
        "year": year,
        "tracknumber": tracknumber,
        "release_mbid": release_mbid,
    }


def get_cover_art(release_mbid):
    if not release_mbid:
        return None
    url = f"https://coverartarchive.org/release/{release_mbid}/front"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except requests.RequestException:
        pass
    return None
