"""YouTube Data API v3 search with Topic-channel + title-match scoring.

We prefer a result where the channel is the artist's "- Topic" channel
AND the video title actually contains the song title. Without the
title-match check, e.g. Maria Chaikovskaya's Topic channel will return
*some* song from her — but maybe not the one we wanted.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import httpx

from app.config import get_settings

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


@dataclass(frozen=True)
class YouTubeMatch:
    video_id: str
    channel_title: str
    video_title: str
    is_topic_match: bool


class YouTubeError(RuntimeError):
    pass


# ----- normalization / scoring helpers -----


_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")


def _normalize(s: str) -> str:
    """Lower-case, strip diacritics, drop punctuation, collapse spaces.

    Used for fuzzy title comparison across Cyrillic + Latin + variants
    (e.g. Мария / Марія, ё / е)."""
    if not s:
        return ""
    # Replace common variants before stripping diacritics.
    s = s.replace("ё", "е").replace("Ё", "Е")
    s = s.replace("і", "и").replace("І", "И")
    s = s.replace("ї", "и").replace("Ї", "И")
    s = s.replace("є", "е").replace("Є", "Е")
    nfkd = unicodedata.normalize("NFKD", s)
    no_combining = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    no_punct = _PUNCT_RE.sub(" ", no_combining)
    return _WS_RE.sub(" ", no_punct).strip().lower()


def _word_overlap(a: str, b: str, min_len: int = 4) -> int:
    """How many ``a`` tokens have a length-``min_len`` prefix found in ``b``.

    Resists declension/transliteration differences — e.g. Russian
    "Чайковская" vs Ukrainian "Чайковська" both share prefix "чайков"."""
    a_toks = [t for t in a.split() if len(t) >= min_len]
    if not a_toks:
        return 0
    return sum(1 for t in a_toks if t[:min_len] in b)


def _strip_parenthetical(title: str) -> str:
    """Drop trailing parentheticals / aliases.

    Examples:
      'Sudno (Boris Rizhy) = Судно (Борис Рижий)' → 'Sudno'
      'Группа крови ( Gruppa Krovi )'              → 'Группа крови'
    """
    cut_positions = [i for i in (title.find("("), title.find("=")) if i != -1]
    if cut_positions:
        return title[: min(cut_positions)].strip()
    return title.strip()


def _title_contains_song(target_title: str, video_title: str) -> bool:
    """True if the normalized song title appears in the normalized video title."""
    tt = _normalize(_strip_parenthetical(target_title))
    if not tt:
        return False
    return tt in _normalize(video_title)


# ----- main entry point -----


def find_video(artist: str, title: str) -> YouTubeMatch | None:
    settings = get_settings()
    if not settings.youtube_api_key:
        raise YouTubeError("YOUTUBE_API_KEY is not configured")

    # Build a clean query: no "topic" keyword, strip parentheticals.
    clean_title = _strip_parenthetical(title)
    query = f"{artist} {clean_title}".strip()

    params = {
        "key": settings.youtube_api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 10,
        "safeSearch": "none",
    }
    with httpx.Client(timeout=15.0) as c:
        r = c.get(SEARCH_URL, params=params)
        if r.status_code != 200:
            raise YouTubeError(f"YouTube API {r.status_code}: {r.text[:200]}")
        data = r.json()

    items = data.get("items") or []
    if not items:
        return None

    artist_norm = _normalize(artist)

    # Score: title-match is the gate, source quality breaks ties.
    # We rank Topic-channel-of-artist > artist's-own-channel > anyone-else,
    # but ONLY among candidates whose video title actually contains the
    # song title. This avoids both the "Topic channel, wrong song" trap
    # (e.g. Maria's Topic for "Целуй меня" when we want "В комнате")
    # AND the "fan upload outranks the artist's own channel because the
    # fan repeated the artist name in their title" trap.
    candidates: list[tuple[int, int, int]] = []  # (score, -index, candidate_id)
    enriched: list[dict] = []
    for i, item in enumerate(items):
        snippet = item.get("snippet") or {}
        vid = (item.get("id") or {}).get("videoId")
        if not vid:
            continue
        channel = snippet.get("channelTitle") or ""
        vtitle = snippet.get("title") or ""

        title_ok = _title_contains_song(title, vtitle)
        is_topic = channel.endswith(" - Topic")
        channel_norm = _normalize(channel.removesuffix(" - Topic"))
        # Artist's own channel: significant word overlap with artist name.
        artist_channel = _word_overlap(artist_norm, channel_norm) >= 1

        if title_ok:
            if is_topic and artist_channel:
                score = 100  # canonical Topic upload by the artist
            elif is_topic:
                score = 90
            elif artist_channel:
                score = 80
            else:
                score = 50  # title matches but unknown source
        else:
            # No title match — last-resort fallback only.
            score = 5 if is_topic else 1

        cid = len(enriched)
        enriched.append(item)
        candidates.append((score, -i, cid))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    score, _idx, cid = candidates[0]
    best = enriched[cid]
    snippet = best["snippet"]
    vid = best["id"]["videoId"]
    channel = snippet.get("channelTitle", "")
    vtitle = snippet.get("title", "")

    # Only call it a "topic match" when the Topic channel result also
    # passes the title check (so the UI banner is honest).
    is_topic = score >= 90

    return YouTubeMatch(
        video_id=vid,
        channel_title=channel,
        video_title=vtitle,
        is_topic_match=is_topic,
    )
