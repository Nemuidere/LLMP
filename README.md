# LLMP — Language-Learning Music Player

A web app that turns songs you actually want to listen to into interactive language-learning sessions. It plays the YouTube video, scrolls the LRC-synced lyrics line by line, shows transliteration and an English translation under each line, and lets you click any word to see its lemma, part of speech, and dictionary definition. When you're ready to drill, it builds an Anki `.apkg` deck of the most-used words from your library.

Supports **Russian** and **Japanese** (with furigana ruby above the kanji + optional romaji tier).

> This is a personal project. I built it because I was learning Russian and bouncing between three browser tabs — YouTube on one, lyrics on another, a dictionary on a third — felt clumsy enough that I just stopped doing the immersion practice. LLMP collapses all of that into one screen so the path of least resistance is the one that actually teaches you something. Japanese support came next for the same reason.

## Features

- **Synced playback** — hidden YouTube player, lyrics highlighted line by line, with manual sync offset stored per-song in your browser.
- **Per-word lookups** — click any word to see lemma, POS, and definition (kaikki.org / Wiktionary).
- **Furigana for Japanese** — hiragana readings rendered as ruby above the kanji; romaji tier toggleable.
- **Translation tier** — English line translations via DeepL (free tier).
- **Anki export** — pick songs from your library, get a `.apkg` deck of the most-used vocab, deduplicated and filtered for grammatical noise.
- **Keyboard-first player** — space to play/pause, arrow keys to seek, `[` / `]` to nudge sync, `+` / `-` to scale font.

## Stack

- **Backend**: FastAPI + SQLAlchemy 2 + SQLite. Russian NLP via pymorphy3 + razdel; Japanese via SudachiPy + pykakasi.
- **Frontend**: React 18 + Vite + TypeScript + Tailwind + React Query.
- **External APIs**: LRCLIB (lyrics, no auth), YouTube Data API v3 (video lookup), DeepL Free (translations).
- **Anki**: `genanki` for `.apkg` generation with deterministic note IDs (re-imports update existing cards instead of duplicating).

## Setup

Requires Docker Engine + the `docker compose` plugin. Tested on Linux / WSL2 Ubuntu.

```bash
# 1. Clone and create your .env
cp .env.example .env
# Fill in YOUTUBE_API_KEY and DEEPL_API_KEY (DEEPL_API_KEY may be left empty
# to disable translations).

# 2. Download the kaikki.org Wiktionary dumps and drop them in backend/data/:
#    - https://kaikki.org/dictionary/Russian/  → kaikki.org-dictionary-Russian.jsonl
#    - https://kaikki.org/dictionary/Japanese/ → kaikki.org-dictionary-Japanese.jsonl

# 3. Bring the stack up
docker compose up --build

# 4. Populate the dictionary table(s) — once per language, takes a few minutes
docker compose exec backend python -m scripts.build_dictionary --language ru
docker compose exec backend python -m scripts.build_dictionary --language ja
```

Then open <http://localhost:5173>.

## Native dev (no Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./backend[dev]
uvicorn app.main:app --reload --app-dir backend

# In another terminal
cd frontend && npm install && npm run dev
```

## Keyboard shortcuts

| Key | Action |
|---|---|
| `space` | play / pause |
| `← / →` | seek ±5s (hold `shift` for ±15s) |
| `[ / ]` | sync ±100ms (hold `shift` for ±500ms) |
| `+ / -` | font scale up / down |
