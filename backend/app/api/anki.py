from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.anki import build_apkg, collect_vocab

router = APIRouter(prefix="/anki", tags=["anki"])

_SUPPORTED = {"ru", "ja"}


class ExportRequest(BaseModel):
    language: str
    song_ids: list[int] = Field(default_factory=list)


class VocabPreview(BaseModel):
    language: str
    count: int
    sample: list[str]


@router.post("/export")
def export_apkg(
    payload: ExportRequest,
    db: Session = Depends(get_db),
) -> Response:
    if payload.language not in _SUPPORTED:
        raise HTTPException(400, f"unsupported language: {payload.language}")
    data = build_apkg(db, payload.language, payload.song_ids or None)
    if not data:
        raise HTTPException(404, "no vocab found for the selected songs")
    filename = f"llmp-{payload.language}.apkg"
    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quote(filename)}"
            )
        },
    )


@router.post("/preview", response_model=VocabPreview)
def preview(payload: ExportRequest, db: Session = Depends(get_db)) -> VocabPreview:
    if payload.language not in _SUPPORTED:
        raise HTTPException(400, f"unsupported language: {payload.language}")
    entries = collect_vocab(db, payload.language, payload.song_ids or None)
    return VocabPreview(
        language=payload.language,
        count=len(entries),
        sample=[e.lemma for e in entries[:8]],
    )
