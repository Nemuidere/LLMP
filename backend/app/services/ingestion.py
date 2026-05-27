"""Background ingestion orchestrator.

Language-aware: the song's language is detected from the LRC text and
drives the NLP, transliteration, and DeepL source-language choices.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Line, Song, Token
from app.services import deepl_client, lrclib, nlp, translit, youtube
from app.services.lang_detect import detect_language

log = logging.getLogger(__name__)


def _set_status(db: Session, song_id: int, status: str, error: str | None = None) -> None:
    song = db.get(Song, song_id)
    if song is None:
        return
    song.ingestion_status = status
    song.ingestion_error = error
    db.commit()


_DEEPL_SOURCE_LANG = {"ru": "RU", "ja": "JA"}


def ingest_song(song_id: int) -> None:
    db = SessionLocal()
    try:
        song = db.get(Song, song_id)
        if song is None:
            log.warning("ingest_song: song %s not found", song_id)
            return
        if song.ingestion_status == "ready":
            return

        try:
            # 1. Pull synced lyrics from LRCLIB.
            record = lrclib.get_by_id(song.lrclib_id)
            synced = record.get("syncedLyrics")
            if not synced:
                raise RuntimeError("LRCLIB record has no syncedLyrics")
            lrc_lines = lrclib.parse_lrc(synced)
            if not lrc_lines:
                raise RuntimeError("Parsed LRC produced no lines")

            # 2. Detect language from the lyric corpus.
            corpus = " ".join(line.text for line in lrc_lines)
            song.language = detect_language(corpus)
            db.commit()

            # 3. YouTube — failure here is non-fatal; we just have no audio.
            try:
                match = youtube.find_video(song.artist, song.title)
            except youtube.YouTubeError as e:
                log.warning("YouTube lookup failed for song %s: %s", song_id, e)
                match = None
            if match:
                song.youtube_video_id = match.video_id
                song.is_topic_match = match.is_topic_match
            else:
                song.is_topic_match = False
            db.commit()

            # 4. Tokenize + lemmatize + transliterate every line (per language).
            analyzed_per_line = [nlp.analyze_line(line.text, song.language) for line in lrc_lines]
            translit_per_line = [translit.to_latin(line.text, song.language) for line in lrc_lines]

            # 5. Batch-translate all line texts.
            translations = deepl_client.translate_lines(
                [line.text for line in lrc_lines],
                source_lang=_DEEPL_SOURCE_LANG.get(song.language, "RU"),
            )

            # 6. Persist Line + Token rows in one transaction.
            db.query(Line).filter(Line.song_id == song.id).delete()
            db.flush()
            for idx, lrc in enumerate(lrc_lines):
                line_row = Line(
                    song_id=song.id,
                    line_index=idx,
                    start_ms=lrc.start_ms,
                    original_text=lrc.text,
                    transliteration=translit_per_line[idx],
                    translation=translations[idx],
                )
                db.add(line_row)
                db.flush()
                for t_idx, tok in enumerate(analyzed_per_line[idx]):
                    db.add(
                        Token(
                            line_id=line_row.id,
                            token_index=t_idx,
                            surface=tok.surface,
                            lemma=tok.lemma,
                            pos=tok.pos,
                            grammar=tok.grammar,
                            is_word=tok.is_word,
                            reading=tok.reading,
                        )
                    )
            song.ingestion_status = "ready"
            song.ingestion_error = None
            db.commit()
            log.info(
                "Ingestion complete for song %s (%s — %s, lang=%s)",
                song.id,
                song.artist,
                song.title,
                song.language,
            )
        except Exception as e:
            log.exception("Ingestion failed for song %s", song_id)
            db.rollback()
            _set_status(db, song_id, "failed", error=str(e)[:500])
    finally:
        db.close()


def sweep_orphans() -> None:
    """Flip rows stuck in ``ingesting`` (e.g. server killed mid-run) to
    ``failed`` so they can be retried via re-ingest."""
    db = SessionLocal()
    try:
        stuck = db.query(Song).filter(Song.ingestion_status == "ingesting").all()
        for song in stuck:
            song.ingestion_status = "failed"
            song.ingestion_error = "Orphaned by server restart"
        if stuck:
            db.commit()
            log.info("Swept %d orphaned ingesting rows on startup", len(stuck))
    finally:
        db.close()
