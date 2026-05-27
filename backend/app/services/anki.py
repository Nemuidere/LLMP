"""Anki deck generation (.apkg) from the user's library.

We aggregate Token rows across the selected songs, drop grammatical
filler via a per-language POS blocklist, require a LemmaDefinition
gloss, and emit one note per (lemma, pos). Note GUIDs are deterministic
so re-importing into an existing collection updates the same cards
instead of duplicating.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO

import genanki
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LemmaDefinition, Line, Song, Token
from app.services.dictionary import candidate_pos

# Stable IDs (any int works; keep them frozen so re-imports update existing
# notes/decks instead of cloning them).
_MODEL_ID = 1_651_290_001
_DECK_BASE_ID = 1_651_290_100

_LANGUAGE_LABEL = {"ru": "Russian", "ja": "Japanese"}

# pymorphy3 POS we treat as grammatical filler (uninteresting as flashcards).
_RU_POS_BLOCK = {"CONJ", "PREP", "PRCL", "INTJ", "NPRO"}

# Sudachi top-level POS to skip (particle / aux / pronoun / conjunction /
# interjection). Punctuation is already is_word=False upstream.
_JA_POS_BLOCK = {"助詞", "助動詞", "代名詞", "接続詞", "感動詞"}

_MIN_LEMMA_LEN = 2


@dataclass(frozen=True)
class VocabEntry:
    lemma: str
    pos: str | None
    reading: str | None
    definition_en: str
    uses: int
    song_count: int


def _model() -> genanki.Model:
    return genanki.Model(
        _MODEL_ID,
        "LLMP Basic",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
            {"name": "Key"},  # used for GUID stability, not displayed
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
            }
        ],
        css=(
            ".card { font-family: -apple-system, system-ui, sans-serif; "
            "font-size: 22px; color: #1a1a1a; background: #fafafa; text-align: center; }"
            ".reading { color: #666; font-size: 16px; margin-top: 4px; }"
            ".pos { color: #888; font-size: 13px; text-transform: uppercase; "
            "letter-spacing: 0.05em; margin-top: 10px; }"
            ".def { color: #1a1a1a; font-size: 18px; margin-top: 8px; }"
            ".meta { color: #999; font-size: 12px; margin-top: 16px; }"
        ),
    )


def _filter_useful(language: str, lemma: str, pos: str | None) -> bool:
    if len(lemma) < _MIN_LEMMA_LEN:
        return False
    if language == "ru" and pos in _RU_POS_BLOCK:
        return False
    return not (language == "ja" and pos in _JA_POS_BLOCK)


def _resolve_definition(
    db: Session, language: str, lemma: str, pos: str | None
) -> LemmaDefinition | None:
    candidates = candidate_pos(pos, language) if pos else ()
    if candidates:
        rows = (
            db.execute(
                select(LemmaDefinition).where(
                    LemmaDefinition.language == language,
                    LemmaDefinition.lemma == lemma,
                    LemmaDefinition.pos.in_(candidates),
                )
            )
            .scalars()
            .all()
        )
        by_pos = {r.pos: r for r in rows}
        for cand in candidates:
            if cand in by_pos:
                return by_pos[cand]
    # Fall back to any POS row for this lemma (better a gloss than none).
    return (
        db.execute(
            select(LemmaDefinition)
            .where(LemmaDefinition.language == language, LemmaDefinition.lemma == lemma)
            .limit(1)
        )
        .scalars()
        .first()
    )


def collect_vocab(
    db: Session, language: str, song_ids: list[int] | None = None
) -> list[VocabEntry]:
    """Aggregate (lemma, pos) usage across the selected songs in one language.

    Songs without a ready ingest are excluded automatically (they have no
    tokens). Sorted by use count desc.
    """
    q = (
        select(Token.lemma, Token.pos, Token.reading, Line.song_id)
        .join(Line, Line.id == Token.line_id)
        .join(Song, Song.id == Line.song_id)
        .where(Song.language == language, Token.is_word.is_(True))
    )
    if song_ids:
        q = q.where(Line.song_id.in_(song_ids))

    # (lemma, pos) -> (uses, set(song_id), first non-empty reading seen)
    agg: dict[tuple[str, str | None], tuple[int, set[int], str | None]] = {}
    for lemma, pos, reading, song_id in db.execute(q).all():
        if not _filter_useful(language, lemma, pos):
            continue
        key = (lemma, pos)
        if key not in agg:
            agg[key] = (1, {song_id}, reading)
        else:
            uses, songs, prev_reading = agg[key]
            songs.add(song_id)
            agg[key] = (uses + 1, songs, prev_reading or reading)

    out: list[VocabEntry] = []
    for (lemma, pos), (uses, songs, reading) in agg.items():
        defn = _resolve_definition(db, language, lemma, pos)
        if defn is None:
            continue
        out.append(
            VocabEntry(
                lemma=lemma,
                pos=pos,
                reading=reading,
                definition_en=defn.definition_en,
                uses=uses,
                song_count=len(songs),
            )
        )
    out.sort(key=lambda v: (-v.uses, v.lemma))
    return out


def _guid_for(language: str, lemma: str, pos: str | None) -> str:
    raw = f"llmp::{language}::{lemma}::{pos or ''}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _render_front(entry: VocabEntry) -> str:
    if entry.reading:
        return f'<div class="lemma">{entry.lemma}</div><div class="reading">{entry.reading}</div>'
    return f'<div class="lemma">{entry.lemma}</div>'


def _render_back(entry: VocabEntry) -> str:
    pos_html = f'<div class="pos">{entry.pos}</div>' if entry.pos else ""
    meta = (
        f'<div class="meta">{entry.uses}× in {entry.song_count} song'
        f"{'s' if entry.song_count != 1 else ''}</div>"
    )
    return f'{pos_html}<div class="def">{entry.definition_en}</div>{meta}'


def build_apkg(db: Session, language: str, song_ids: list[int] | None = None) -> bytes:
    if language not in _LANGUAGE_LABEL:
        raise ValueError(f"unsupported language: {language}")

    entries = collect_vocab(db, language, song_ids)

    model = _model()
    deck_id = _DECK_BASE_ID + (1 if language == "ru" else 2)
    deck = genanki.Deck(deck_id, f"LLMP · {_LANGUAGE_LABEL[language]}")

    for e in entries:
        guid = _guid_for(language, e.lemma, e.pos)
        note = genanki.Note(
            model=model,
            fields=[_render_front(e), _render_back(e), guid],
            guid=guid,
        )
        deck.add_note(note)

    buf = BytesIO()
    genanki.Package(deck).write_to_file(buf)
    return buf.getvalue()
