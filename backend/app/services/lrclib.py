"""LRCLIB client + LRC timestamp parser.

API docs: https://lrclib.net/docs
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

BASE_URL = "https://lrclib.net/api"
USER_AGENT = "LLMP/0.1 (https://github.com/Nemuidere/LLMP)"

_TIMESTAMP_RE = re.compile(r"\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]")


@dataclass(frozen=True)
class LrcLine:
    start_ms: int
    text: str


@dataclass(frozen=True)
class LrclibTrack:
    id: int
    track_name: str
    artist_name: str
    album_name: str | None
    duration: float | None
    has_synced: bool


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=15.0,
    )


def search(query: str, limit: int = 10) -> list[LrclibTrack]:
    """Search LRCLIB, return only results that have synced lyrics."""
    if not query.strip():
        return []
    with _client() as c:
        r = c.get("/search", params={"q": query})
        r.raise_for_status()
        rows = r.json()
    out: list[LrclibTrack] = []
    for row in rows:
        if not row.get("syncedLyrics"):
            continue
        out.append(
            LrclibTrack(
                id=row["id"],
                track_name=row.get("trackName") or "",
                artist_name=row.get("artistName") or "",
                album_name=row.get("albumName"),
                duration=row.get("duration"),
                has_synced=True,
            )
        )
        if len(out) >= limit:
            break
    return out


def get_by_id(lrclib_id: int) -> dict:
    with _client() as c:
        r = c.get(f"/get/{lrclib_id}")
        r.raise_for_status()
        return r.json()


def parse_lrc(synced_lyrics: str) -> list[LrcLine]:
    """Parse LRC text into ordered (start_ms, text) lines.

    Skips empty lines and entries without any timestamp tag. A line with
    multiple timestamps yields one LrcLine per timestamp.
    """
    out: list[LrcLine] = []
    for raw in synced_lyrics.splitlines():
        stamps = list(_TIMESTAMP_RE.finditer(raw))
        if not stamps:
            continue
        text = _TIMESTAMP_RE.sub("", raw).strip()
        if not text:
            # Pure instrumental marker line — still keep timing so the
            # player can advance, but with empty text.
            pass
        for m in stamps:
            mm, ss, frac = m.group(1), m.group(2), m.group(3) or "0"
            # Normalize fractional seconds to milliseconds.
            frac_ms = int(frac.ljust(3, "0")[:3])
            ms = (int(mm) * 60 + int(ss)) * 1000 + frac_ms
            out.append(LrcLine(start_ms=ms, text=text))
    out.sort(key=lambda x: x.start_ms)
    return out
