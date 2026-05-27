"""Japanese → Hepburn romaji via pykakasi."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _kks():
    import pykakasi

    return pykakasi.kakasi()


def to_latin(text: str) -> str:
    if not text:
        return ""
    parts = _kks().convert(text)
    return " ".join(p["hepburn"] for p in parts if p.get("hepburn"))
