"""Language-dispatching NLP layer.

Each implementation (``ru``, ``ja``) returns the same :class:`AnalyzedToken`
shape so the ingestion pipeline doesn't need per-language branches.
"""

from __future__ import annotations

from app.services.nlp.types import AnalyzedToken


def analyze_line(text: str, language: str) -> list[AnalyzedToken]:
    if language == "ja":
        from app.services.nlp import ja

        return ja.analyze_line(text)
    # Default + ``"ru"`` use Russian.
    from app.services.nlp import ru

    return ru.analyze_line(text)


__all__ = ["AnalyzedToken", "analyze_line"]
