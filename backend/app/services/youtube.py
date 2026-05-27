"""YouTube Data API v3 search with " - Topic" channel preference."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.config import get_settings

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


@dataclass(frozen=True)
class YouTubeMatch:
    video_id: str
    channel_title: str
    is_topic_match: bool


class YouTubeError(RuntimeError):
    pass


def find_video(artist: str, title: str) -> YouTubeMatch | None:
    settings = get_settings()
    if not settings.youtube_api_key:
        raise YouTubeError("YOUTUBE_API_KEY is not configured")

    query = f"{artist} {title} topic"
    params = {
        "key": settings.youtube_api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 5,
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

    # Prefer a result whose channel ends with " - Topic".
    for item in items:
        snippet = item.get("snippet") or {}
        channel = snippet.get("channelTitle") or ""
        vid = (item.get("id") or {}).get("videoId")
        if vid and channel.endswith(" - Topic"):
            return YouTubeMatch(video_id=vid, channel_title=channel, is_topic_match=True)

    # Fallback: first result with a videoId.
    for item in items:
        snippet = item.get("snippet") or {}
        vid = (item.get("id") or {}).get("videoId")
        if vid:
            return YouTubeMatch(
                video_id=vid,
                channel_title=snippet.get("channelTitle") or "",
                is_topic_match=False,
            )
    return None
