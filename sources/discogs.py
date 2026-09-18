import requests

SEARCH_URL = "https://api.discogs.com/database/search"
RELEASE_URL = "https://api.discogs.com/releases/{release_id}"

# Fields this module knows how to fill in from Discogs data
FILLABLE_FIELDS = ("genre", "year", "tracknumber")


def search_discogs(artist_hint, title_hint, token):
    params = {
        "type": "release",
        "token": token,
    }
    if artist_hint:
        params["artist"] = artist_hint
    if title_hint:
        params["track"] = title_hint
    if not artist_hint and not title_hint:
        return None

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    results = response.json().get("results", [])
    return results[0] if results else None


def get_release_details(release_id, token):
    try:
        response = requests.get(
            RELEASE_URL.format(release_id=release_id),
            params={"token": token},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}


def fill_missing_fields(proposed, artist_hint, title_hint, token):
    """
    Given the metadata dict MusicBrainz already produced, query Discogs
    only if something in FILLABLE_FIELDS is still empty, and only fill
    in those specific gaps -- everything MusicBrainz already found is
    left untouched.
    """
    missing = [f for f in FILLABLE_FIELDS if not proposed.get(f)]
    if not missing or not token:
        return proposed

    result = search_discogs(
        artist_hint or proposed.get("artist", ""),
        title_hint or proposed.get("title", ""),
        token,
    )
    if not result:
        return proposed

    release_id = result.get("id")
    details = get_release_details(release_id, token) if release_id else {}

    if "genre" in missing:
        genres = details.get("genres") or result.get("genre") or []
        styles = details.get("styles") or result.get("style") or []
        combined = list(genres) + list(styles)
        if combined:
            proposed["genre"] = combined[0]

    if "year" in missing:
        year = details.get("year") or result.get("year")
        if year:
            proposed["year"] = str(year)

    if "tracknumber" in missing:
        target_title = (title_hint or proposed.get("title", "")).strip().lower()
        for index, track in enumerate(details.get("tracklist", []), start=1):
            if track.get("title", "").strip().lower() == target_title:
                proposed["tracknumber"] = track.get("position") or str(index)
                break

    return proposed
