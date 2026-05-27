from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyzedToken:
    surface: str
    lemma: str
    pos: str | None
    grammar: str | None
    is_word: bool
    # Hiragana reading for Japanese tokens. Always ``None`` for Russian.
    reading: str | None = None
