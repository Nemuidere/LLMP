"""Effective-offset computation for a song.

Median of submissions when count ≥ ``offset_min_submissions`` (and the
feature is enabled), else 0. Per AGENTS.md §3 the threshold is wired to
config so we can toggle community correction during dev.
"""

from __future__ import annotations

from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import OffsetSubmission


def effective_offset_ms(db: Session, song_id: int) -> int:
    settings = get_settings()
    if not settings.offset_enabled:
        return 0
    rows = (
        db.execute(select(OffsetSubmission.offset_ms).where(OffsetSubmission.song_id == song_id))
        .scalars()
        .all()
    )
    if len(rows) < settings.offset_min_submissions:
        return 0
    return int(median(rows))
