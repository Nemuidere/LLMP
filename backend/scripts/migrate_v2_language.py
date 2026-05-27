"""One-shot schema migration for the v2 Japanese-support changes.

What this does to an existing SQLite DB:

1. Adds a nullable ``reading`` column to ``tokens`` if missing.
2. Rebuilds ``lemma_definitions`` so the primary key is
   ``(language, lemma, pos)`` instead of ``(lemma, pos)``. Existing rows
   are preserved and backfilled with ``language='ru'``.

Idempotent — running it twice on an already-migrated DB is a no-op.

Usage (inside the backend container or local venv)::

    python -m scripts.migrate_v2_language
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db import engine


def _column_names(conn, table: str) -> set[str]:
    return {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).all()}


def _pk_columns(conn, table: str) -> list[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).all()
    return [r[1] for r in rows if r[5]]  # pk flag is column index 5


def main() -> int:
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    with engine.begin() as conn:
        # ---- 1. tokens.reading ----
        if "tokens" in tables:
            cols = _column_names(conn, "tokens")
            if "reading" not in cols:
                print("Adding tokens.reading …")
                conn.execute(text("ALTER TABLE tokens ADD COLUMN reading VARCHAR(128)"))
            else:
                print("tokens.reading already present, skipping")

        # ---- 2. lemma_definitions PK rebuild ----
        if "lemma_definitions" in tables:
            pk = _pk_columns(conn, "lemma_definitions")
            if pk != ["language", "lemma", "pos"]:
                print("Rebuilding lemma_definitions with composite PK (language, lemma, pos) …")
                conn.execute(
                    text(
                        """
                        CREATE TABLE lemma_definitions_new (
                            language VARCHAR(8) NOT NULL,
                            lemma VARCHAR(128) NOT NULL,
                            pos VARCHAR(16) NOT NULL,
                            definition_en TEXT,
                            examples TEXT,
                            PRIMARY KEY (language, lemma, pos)
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO lemma_definitions_new
                            (language, lemma, pos, definition_en, examples)
                        SELECT 'ru', lemma, pos, definition_en, examples
                        FROM lemma_definitions
                        """
                    )
                )
                conn.execute(text("DROP TABLE lemma_definitions"))
                conn.execute(text("ALTER TABLE lemma_definitions_new RENAME TO lemma_definitions"))
                cnt = conn.execute(text("SELECT COUNT(*) FROM lemma_definitions")).scalar()
                print(f"  lemma_definitions now has {cnt} rows (backfilled language='ru').")
            else:
                print("lemma_definitions PK already (language, lemma, pos), skipping")

    print("Migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
