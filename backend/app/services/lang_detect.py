"""Trivial script-based language detector.

We only support Russian + Japanese in v2. The heuristic: count code-point
hits in each script and pick the dominant one. Defaults to Russian when
neither dominates.
"""

from __future__ import annotations


def _count_in_ranges(text: str, ranges: list[tuple[str, str]]) -> int:
    n = 0
    for c in text:
        for lo, hi in ranges:
            if lo <= c <= hi:
                n += 1
                break
    return n


_CYRILLIC = [("Ѐ", "ӿ")]
_JAPANESE = [
    ("぀", "ゟ"),  # Hiragana
    ("゠", "ヿ"),  # Katakana
    ("一", "鿿"),  # CJK Unified Ideographs
]


def detect_language(text: str) -> str:
    cyr = _count_in_ranges(text, _CYRILLIC)
    jp = _count_in_ranges(text, _JAPANESE)
    if jp > cyr:
        return "ja"
    return "ru"
