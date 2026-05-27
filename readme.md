# LLMP — Language-Learning Music Player

Russian-first web app that teaches via synced music: hidden YouTube player + LRC lyrics, with per-word lemma lookups and line translations.

> The full project spec lives in `AGENTS.md` (gitignored). Anything below is just the local-dev quickstart.

## Requirements

- Linux / WSL Ubuntu (tested on WSL2, kernel 6.6.x)
- Python 3.11+ (`python3 --version`)
- Docker Engine + `docker compose` plugin (`docker --version` / `docker compose version`)
- Node 18+ for the frontend (when it lands)

## First-time setup

```bash
# 1. Clone, then create + populate the .env from the example
cp .env.example .env
# Fill in YOUTUBE_API_KEY and DEEPL_API_KEY in .env

# 2. Place the kaikki.org Russian Wiktionary JSONL dump at:
#    backend/data/kaikki.org-dictionary-Russian.jsonl
#    (download once from https://kaikki.org/dictionary/Russian/)
```

## Local dev — option A: native venv (fastest iteration)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./backend[dev]

# Run the API
uvicorn app.main:app --reload --app-dir backend

# Smoke check
curl http://localhost:8000/api/health
```

Populate the dictionary table once (takes a few minutes):

```bash
cd backend && python -m scripts.build_dictionary
```

## Local dev — option B: Docker (parity with deploy)

```bash
docker compose up --build backend
# logs stream; the API is at http://localhost:8000

# In another terminal, populate the dictionary inside the container:
docker compose exec backend python -m scripts.build_dictionary
```

The `backend/data/` directory is volume-mounted so the SQLite file and the kaikki JSONL persist across rebuilds. The `app/` and `scripts/` folders are also mounted, so edits hot-reload via uvicorn `--reload`.

## Manual end-to-end smoke test

```bash
# 1. Search
curl 'http://localhost:8000/api/songs/autocomplete?q=Gruppa+krovi'

# 2. Pick an lrclib_id from the response, then ingest
curl -X POST http://localhost:8000/api/songs/ingest \
  -H 'Content-Type: application/json' \
  -d '{"lrclib_id": 12345, "artist": "Кино", "title": "Группа крови"}'

# 3. Poll status until "ready"
curl http://localhost:8000/api/songs/1/status

# 4. Fetch the full song
curl http://localhost:8000/api/songs/1
```

## Code style

`ruff` is the formatter + linter. Run before committing:

```bash
.venv/bin/ruff format backend/
.venv/bin/ruff check backend/
```
