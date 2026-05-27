from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import OffsetSubmission, Song
from app.services.offsets import effective_offset_ms
from app.services.rate_limit import hash_ip, offset_limiter

router = APIRouter(prefix="/songs", tags=["offsets"])


class OffsetIn(BaseModel):
    offset_ms: int = Field(ge=-30000, le=30000)


class OffsetOut(BaseModel):
    song_id: int
    effective_offset_ms: int
    submission_count: int


@router.post("/{song_id}/offset", response_model=OffsetOut)
def submit_offset(
    song_id: int,
    payload: OffsetIn,
    request: Request,
    db: Session = Depends(get_db),
) -> OffsetOut:
    song = db.get(Song, song_id)
    if song is None:
        raise HTTPException(404, "Song not found")

    client_ip = request.client.host if request.client else "unknown"
    ip_h = hash_ip(client_ip)
    if not offset_limiter.allow(ip_h):
        raise HTTPException(429, "Too many offset submissions, try again later")

    db.add(
        OffsetSubmission(
            song_id=song.id,
            offset_ms=payload.offset_ms,
            submitter_ip_hash=ip_h,
        )
    )
    db.commit()

    count = db.query(OffsetSubmission).filter(OffsetSubmission.song_id == song.id).count()
    return OffsetOut(
        song_id=song.id,
        effective_offset_ms=effective_offset_ms(db, song.id),
        submission_count=count,
    )
