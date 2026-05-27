from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True)
    artist: Mapped[str] = mapped_column(String(256), index=True)
    title: Mapped[str] = mapped_column(String(256), index=True)
    language: Mapped[str] = mapped_column(String(8), default="ru")
    youtube_video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_topic_match: Mapped[bool] = mapped_column(Boolean, default=False)
    ingestion_status: Mapped[str] = mapped_column(String(16), default="ingesting")
    ingestion_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    lrclib_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    lines: Mapped[list["Line"]] = relationship(
        back_populates="song", cascade="all, delete-orphan", order_by="Line.line_index"
    )
    offset_submissions: Mapped[list["OffsetSubmission"]] = relationship(
        back_populates="song", cascade="all, delete-orphan"
    )


class Line(Base):
    __tablename__ = "lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"), index=True)
    line_index: Mapped[int] = mapped_column(Integer)
    start_ms: Mapped[int] = mapped_column(Integer)
    original_text: Mapped[str] = mapped_column(Text)
    transliteration: Mapped[str] = mapped_column(Text, default="")
    translation: Mapped[str | None] = mapped_column(Text, nullable=True)

    song: Mapped[Song] = relationship(back_populates="lines")
    tokens: Mapped[list["Token"]] = relationship(
        back_populates="line", cascade="all, delete-orphan", order_by="Token.token_index"
    )

    __table_args__ = (Index("ix_lines_song_idx", "song_id", "line_index", unique=True),)


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("lines.id", ondelete="CASCADE"), index=True)
    token_index: Mapped[int] = mapped_column(Integer)
    surface: Mapped[str] = mapped_column(String(128))
    lemma: Mapped[str] = mapped_column(String(128), index=True)
    pos: Mapped[str | None] = mapped_column(String(16), nullable=True)
    grammar: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_word: Mapped[bool] = mapped_column(Boolean, default=True)

    line: Mapped[Line] = relationship(back_populates="tokens")


class LemmaDefinition(Base):
    __tablename__ = "lemma_definitions"

    lemma: Mapped[str] = mapped_column(String(128), primary_key=True)
    pos: Mapped[str] = mapped_column(String(16), primary_key=True)
    definition_en: Mapped[str] = mapped_column(Text)
    examples: Mapped[str | None] = mapped_column(Text, nullable=True)


class OffsetSubmission(Base):
    __tablename__ = "offset_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"), index=True)
    offset_ms: Mapped[int] = mapped_column(Integer)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    submitter_ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    song: Mapped[Song] = relationship(back_populates="offset_submissions")
