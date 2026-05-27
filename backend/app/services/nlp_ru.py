"""Russian tokenization + lemmatization.

Uses razdel for tokenization and pymorphy3 for morphological analysis.
The MorphAnalyzer loads ~30MB of dict data so we initialize lazily and
reuse the singleton across calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from razdel import tokenize


@dataclass(frozen=True)
class AnalyzedToken:
    surface: str
    lemma: str
    pos: str | None
    grammar: str | None
    is_word: bool


@lru_cache(maxsize=1)
def _analyzer():
    import pymorphy3

    return pymorphy3.MorphAnalyzer(lang="ru")


def _is_word(s: str) -> bool:
    return any(ch.isalpha() for ch in s)


def analyze_line(text: str) -> list[AnalyzedToken]:
    if not text.strip():
        return []
    morph = _analyzer()
    out: list[AnalyzedToken] = []
    for tok in tokenize(text):
        surface = tok.text
        if not _is_word(surface):
            out.append(
                AnalyzedToken(surface=surface, lemma=surface, pos=None, grammar=None, is_word=False)
            )
            continue
        parses = morph.parse(surface)
        top = parses[0] if parses else None
        if top is None:
            out.append(
                AnalyzedToken(
                    surface=surface,
                    lemma=surface.lower(),
                    pos=None,
                    grammar=None,
                    is_word=True,
                )
            )
            continue
        tag_str = str(top.tag)
        pos = top.tag.POS
        out.append(
            AnalyzedToken(
                surface=surface,
                lemma=top.normal_form,
                pos=pos,
                grammar=tag_str,
                is_word=True,
            )
        )
    return out
