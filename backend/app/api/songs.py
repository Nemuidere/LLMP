from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LemmaDefinition, Line, Song, Token
from app.services import dictionary, ingestion, lrclib
from app.services.offsets import effective_offset_ms

router = APIRouter(prefix="/songs", tags=["songs"])


# ----- Schemas -----


class AutocompleteHit(BaseModel):
    lrclib_id: int
    track_name: str
    artist_name: str
    album_name: str | None
    duration: float | None


class IngestRequest(BaseModel):
    lrclib_id: int
    artist: str
    title: str


class IngestResponse(BaseModel):
    song_id: int
    status: str


class StatusResponse(BaseModel):
    song_id: int
    status: str
    error: str | None = None


class TokenOut(BaseModel):
    surface: str
    lemma: str
    pos: str | None
    grammar: str | None
    is_word: bool
    definition_en: str | None = None


class LineOut(BaseModel):
    line_index: int
    start_ms: int
    original_text: str
    transliteration: str
    translation: str | None
    tokens: list[TokenOut]


class SongOut(BaseModel):
    id: int
    artist: str
    title: str
    language: str
    youtube_video_id: str | None
    is_topic_match: bool
    ingestion_status: str
    effective_offset_ms: int
    lines: list[LineOut] = Field(default_factory=list)


# ----- Routes -----


@router.get("/autocomplete", response_model=list[AutocompleteHit])
def autocomplete(q: str) -> list[AutocompleteHit]:
    hits = lrclib.search(q.strip(), limit=10)
    return [
        AutocompleteHit(
            lrclib_id=h.id,
            track_name=h.track_name,
            artist_name=h.artist_name,
            album_name=h.album_name,
            duration=h.duration,
        )
        for h in hits
    ]


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    payload: IngestRequest, background: BackgroundTasks, db: Session = Depends(get_db)
) -> IngestResponse:
    existing = db.execute(
        select(Song).where(Song.lrclib_id == payload.lrclib_id)
    ).scalar_one_or_none()
    if existing:
        if existing.ingestion_status == "failed":
            existing.ingestion_status = "ingesting"
            existing.ingestion_error = None
            db.commit()
            background.add_task(ingestion.ingest_song, existing.id)
        return IngestResponse(song_id=existing.id, status=existing.ingestion_status)

    song = Song(
        artist=payload.artist,
        title=payload.title,
        language="ru",
        lrclib_id=payload.lrclib_id,
        ingestion_status="ingesting",
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    background.add_task(ingestion.ingest_song, song.id)
    return IngestResponse(song_id=song.id, status="ingesting")


@router.get("/{song_id}/status", response_model=StatusResponse)
def status(song_id: int, db: Session = Depends(get_db)) -> StatusResponse:
    song = db.get(Song, song_id)
    if song is None:
        raise HTTPException(404, "Song not found")
    return StatusResponse(song_id=song.id, status=song.ingestion_status, error=song.ingestion_error)


@router.get("/{song_id}", response_model=SongOut)
def get_song(song_id: int, db: Session = Depends(get_db)) -> SongOut:
    song = db.get(Song, song_id)
    if song is None:
        raise HTTPException(404, "Song not found")

    # Fetch lines + tokens. For "ready" songs build the nested response;
    # for "ingesting"/"failed" return metadata only so the client can
    # poll status without scrolling through partial rows.
    lines_out: list[LineOut] = []
    if song.ingestion_status == "ready":
        lines = (
            db.execute(select(Line).where(Line.song_id == song.id).order_by(Line.line_index))
            .scalars()
            .all()
        )
        # Bulk-load token rows.
        line_ids = [line.id for line in lines]
        tokens_by_line: dict[int, list[Token]] = {lid: [] for lid in line_ids}
        if line_ids:
            tok_rows = (
                db.execute(
                    select(Token)
                    .where(Token.line_id.in_(line_ids))
                    .order_by(Token.line_id, Token.token_index)
                )
                .scalars()
                .all()
            )
            for tok in tok_rows:
                tokens_by_line[tok.line_id].append(tok)

        # Bulk-load definitions for every distinct lemma in one query.
        lemmas = {tok.lemma for toks in tokens_by_line.values() for tok in toks if tok.is_word}
        defs: dict[tuple[str, str], LemmaDefinition] = {}
        if lemmas:
            for row in (
                db.execute(select(LemmaDefinition).where(LemmaDefinition.lemma.in_(lemmas)))
                .scalars()
                .all()
            ):
                defs[(row.lemma, row.pos)] = row

        for line in lines:
            tokens_out: list[TokenOut] = []
            for tok in tokens_by_line.get(line.id, []):
                definition: str | None = None
                if tok.is_word:
                    wpos = dictionary.normalize_pos(tok.pos)
                    row = defs.get((tok.lemma, wpos)) if wpos else None
                    if row is None:
                        # Fallback: any POS row for that lemma.
                        for (lemma, _pos), candidate in defs.items():
                            if lemma == tok.lemma:
                                row = candidate
                                break
                    if row is not None:
                        definition = row.definition_en
                tokens_out.append(
                    TokenOut(
                        surface=tok.surface,
                        lemma=tok.lemma,
                        pos=tok.pos,
                        grammar=tok.grammar,
                        is_word=tok.is_word,
                        definition_en=definition,
                    )
                )
            lines_out.append(
                LineOut(
                    line_index=line.line_index,
                    start_ms=line.start_ms,
                    original_text=line.original_text,
                    transliteration=line.transliteration,
                    translation=line.translation,
                    tokens=tokens_out,
                )
            )

    return SongOut(
        id=song.id,
        artist=song.artist,
        title=song.title,
        language=song.language,
        youtube_video_id=song.youtube_video_id,
        is_topic_match=song.is_topic_match,
        ingestion_status=song.ingestion_status,
        effective_offset_ms=effective_offset_ms(db, song.id),
        lines=lines_out,
    )
