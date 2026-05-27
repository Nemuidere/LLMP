"""One-time loader: kaikki.org Russian Wiktionary JSONL → LemmaDefinition.

Run with the backend venv active::

    python -m scripts.build_dictionary [path/to/kaikki.jsonl]

Streams the file line-by-line; does not load the full 300MB into memory.
Idempotent: existing rows for (lemma, pos) are replaced.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.config import BACKEND_DIR
from app.db import SessionLocal, init_db
from app.models import LemmaDefinition

DEFAULT_PATH = BACKEND_DIR / "data" / "kaikki.org-dictionary-Russian.jsonl"
BATCH_SIZE = 2000


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
    return out[:5]  # cap to keep rows small


def iter_rows(path: Path):
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
                "lemma": lemma,
                "pos": pos,
                "definition_en": "; ".join(glosses[:5]),
                "examples": json.dumps(_examples_for(entry), ensure_ascii=False) or None,
            }


def main(path_arg: str | None = None) -> int:
    path = Path(path_arg) if path_arg else DEFAULT_PATH
    if not path.exists():
        print(f"Dictionary file not found: {path}", file=sys.stderr)
        return 2

    init_db()
    db = SessionLocal()
    inserted = 0
    batch: list[dict] = []

    try:
        for row in iter_rows(path):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                stmt = sqlite_insert(LemmaDefinition).values(batch)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["lemma", "pos"],
                    set_={
                        "definition_en": stmt.excluded.definition_en,
                        "examples": stmt.excluded.examples,
                    },
                )
                db.execute(stmt)
                db.commit()
                inserted += len(batch)
                batch.clear()
                if inserted % 20000 == 0:
                    print(f"... {inserted} rows")

        if batch:
            stmt = sqlite_insert(LemmaDefinition).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["lemma", "pos"],
                set_={
                    "definition_en": stmt.excluded.definition_en,
                    "examples": stmt.excluded.examples,
                },
            )
            db.execute(stmt)
            db.commit()
            inserted += len(batch)

        total = db.query(LemmaDefinition).count()
        print(f"Done. Upserted {inserted} rows; table now has {total} entries.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
