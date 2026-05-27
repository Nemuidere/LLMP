"""Lemma → definition lookup against the LemmaDefinition table.

The table is populated by ``scripts/build_dictionary.py`` from the
kaikki.org Russian Wiktionary JSONL dump.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LemmaDefinition

# pymorphy3 POS tags → Wiktionary part-of-speech labels. Keep this loose;
# fallbacks below recover when the tag doesn't match exactly.
_POS_MAP = {
    "NOUN": "noun",
    "VERB": "verb",
    "INFN": "verb",
    "ADJF": "adj",
    "ADJS": "adj",
    "COMP": "adj",
    "ADVB": "adv",
    "NPRO": "pron",
    "PRED": "adv",
    "PREP": "prep",
    "CONJ": "conj",
    "PRCL": "particle",
    "INTJ": "intj",
    "NUMR": "num",
}


def normalize_pos(pymorphy_pos: str | None) -> str | None:
    if not pymorphy_pos:
        return None
    return _POS_MAP.get(pymorphy_pos)


def lookup(db: Session, lemma: str, pos: str | None = None) -> LemmaDefinition | None:
    if not lemma:
        return None
    wiktionary_pos = normalize_pos(pos)
    stmt = select(LemmaDefinition).where(LemmaDefinition.lemma == lemma)
    if wiktionary_pos:
        row = db.execute(stmt.where(LemmaDefinition.pos == wiktionary_pos)).scalar_one_or_none()
        if row:
            return row
    # Fallback: any POS row for that lemma.
    return db.execute(stmt.limit(1)).scalar_one_or_none()
