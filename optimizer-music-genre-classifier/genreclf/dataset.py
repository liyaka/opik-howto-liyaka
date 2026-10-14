"""The labelled songs: fictional descriptions, one of six genres each."""

import json
from pathlib import Path

GENRES = ("classical", "jazz", "folk", "metal", "electronic", "hip-hop")
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "songs.json"


def load_songs(path: Path = DATA_FILE) -> list[dict]:
    """Return [{"song": ..., "genre": ...}, ...] and check the labels."""
    songs = json.loads(path.read_text(encoding="utf-8"))
    for song in songs:
        if song["genre"] not in GENRES:
            raise ValueError(f"unknown genre {song['genre']!r}")
    return songs
