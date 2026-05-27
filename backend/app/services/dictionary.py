"""Lemma → definition lookup against the LemmaDefinition table.

Per-language dispatch on POS candidates:
- Russian: pymorphy3 POS tags → kaikki (Russian Wiktionary) POS labels
- Japanese: SudachiPy top-level POS → kaikki (Japanese Wiktionary) POS labels

The table is populated by ``scripts/build_dictionary.py`` from kaikki.org's
pre-parsed JSONL dumps.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LemmaDefinition

# ----- Russian (pymorphy3 POS → kaikki POS) -----

_RU_POS_CANDIDATES: dict[str, tuple[str, ...]] = {
    "NOUN": ("noun",),
    "VERB": ("verb",),
    "INFN": ("verb",),
    "ADJF": ("adj", "pron"),
    "ADJS": ("adj", "pron"),
    "COMP": ("adj",),
    "ADVB": ("adv",),
    "NPRO": ("pron",),
    "PRED": ("adv",),
    "PREP": ("prep",),
    "CONJ": ("conj",),
    "PRCL": ("particle",),
    "INTJ": ("intj",),
    "NUMR": ("num",),
    "PRTF": ("verb",),
    "PRTS": ("verb",),
    "GRND": ("verb",),
}


def candidate_pos(pymorphy_pos: str | None, language: str = "ru") -> tuple[str, ...]:
    if not pymorphy_pos:
        return ()
    if language == "ja":
        from app.services.nlp.ja import candidate_kaikki_pos

        return candidate_kaikki_pos(pymorphy_pos)
    return _RU_POS_CANDIDATES.get(pymorphy_pos, ())


def normalize_pos(pymorphy_pos: str | None, language: str = "ru") -> str | None:
    """Backwards-compatible single-value lookup (first candidate only)."""
    cands = candidate_pos(pymorphy_pos, language)
    return cands[0] if cands else None


def lookup(
    db: Session, lemma: str, pos: str | None = None, language: str = "ru"
) -> LemmaDefinition | None:
    if not lemma:
        return None
    stmt_base = select(LemmaDefinition).where(
        LemmaDefinition.language == language,
        LemmaDefinition.lemma == lemma,
    )
    for cand in candidate_pos(pos, language):
        row = db.execute(stmt_base.where(LemmaDefinition.pos == cand)).scalar_one_or_none()
        if row:
            return row
    return db.execute(stmt_base.limit(1)).scalar_one_or_none()
