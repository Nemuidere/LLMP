"""One-time loader: kaikki.org Wiktionary JSONL → LemmaDefinition.

Run from the backend container or local venv::

    python -m scripts.build_dictionary --language ru [path/to/kaikki-ru.jsonl]
    python -m scripts.build_dictionary --language ja [path/to/kaikki-ja.jsonl]

Default file paths:
    Russian: backend/data/kaikki.org-dictionary-Russian.jsonl
    Japanese: backend/data/kaikki.org-dictionary-Japanese.jsonl

Streams the file line-by-line; does not load the full dump into memory.
Idempotent: existing rows for ``(language, lemma, pos)`` are replaced.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.config import BACKEND_DIR
from app.db import SessionLocal, init_db
from app.models import LemmaDefinition

BATCH_SIZE = 2000

_DEFAULT_PATHS = {
    "ru": BACKEND_DIR / "data" / "kaikki.org-dictionary-Russian.jsonl",
    "ja": BACKEND_DIR / "data" / "kaikki.org-dictionary-Japanese.jsonl",
}


def _glosses_for(entry: dict) -> list[str]:
    out: list[str] = []
    for sense in entry.get("senses") or []:
        for g in sense.get("glosses") or []:
            if isinstance(g, str) and g.strip():
                out.append(g.strip())
    return out


def _examples_for(entry: dict) -> list[dict]:
    out: list[dict] = []
    for sense in entry.get("senses") or []:
        for ex in sense.get("examples") or []:
            if isinstance(ex, dict):
                out.append({"text": ex.get("text"), "english": ex.get("english")})
    return out[:5]


def iter_rows(path: Path, language: str) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            lemma = entry.get("word")
            pos = entry.get("pos")
            if not lemma or not pos:
                continue
            glosses = _glosses_for(entry)
            if not glosses:
                continue
            yield {
                "language": language,
                "lemma": lemma,
                "pos": pos,
                "definition_en": "; ".join(glosses[:5]),
                "examples": json.dumps(_examples_for(entry), ensure_ascii=False) or None,
            }


def _flush(db, batch: list[dict]) -> None:
    stmt = sqlite_insert(LemmaDefinition).values(batch)
    stmt = stmt.on_conflict_do_update(
        index_elements=["language", "lemma", "pos"],
        set_={
            "definition_en": stmt.excluded.definition_en,
            "examples": stmt.excluded.examples,
        },
    )
    db.execute(stmt)
    db.commit()


def main(language: str, path_arg: str | None = None) -> int:
    path = Path(path_arg) if path_arg else _DEFAULT_PATHS[language]
    if not path.exists():
        print(f"Dictionary file not found: {path}", file=sys.stderr)
        return 2

    init_db()
    db = SessionLocal()
    inserted = 0
    batch: list[dict] = []

    try:
        for row in iter_rows(path, language):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                _flush(db, batch)
                inserted += len(batch)
                batch.clear()
                if inserted % 20000 == 0:
                    print(f"... {inserted} rows")
        if batch:
            _flush(db, batch)
            inserted += len(batch)

        total = db.query(LemmaDefinition).filter(LemmaDefinition.language == language).count()
        print(f"Done. Upserted {inserted} rows; {language!r} table has {total} entries.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=["ru", "ja"], default="ru")
    parser.add_argument("path", nargs="?", default=None)
    args = parser.parse_args()
    raise SystemExit(main(args.language, args.path))
