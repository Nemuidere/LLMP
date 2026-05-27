"""DeepL translation wrapper. Free-tier keys end in ':fx'; the deepl
package auto-routes them to the free endpoint."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings

CHUNK_SIZE = 50  # AGENTS.md §Ingestion step 4


class DeeplDisabled(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _translator():
    import deepl

    key = get_settings().deepl_api_key
    if not key:
        raise DeeplDisabled("DEEPL_API_KEY not set")
    return deepl.Translator(key)


def is_enabled() -> bool:
    s = get_settings()
    return bool(s.deepl_api_key)


def translate_lines(
    texts: list[str], source_lang: str = "RU", target_lang: str = "EN-US"
) -> list[str | None]:
    """Translate a list of lines, preserving order. Empty inputs → None.

    Returns ``None`` for each line if DeepL is disabled/unconfigured —
    callers persist this as a null translation. The ingestion pipeline
    should treat translation as best-effort, not blocking.
    """
    if not is_enabled():
        return [None] * len(texts)

    # Map non-empty indices so we don't waste quota on blank lines.
    indices = [i for i, t in enumerate(texts) if t and t.strip()]
    if not indices:
        return [None] * len(texts)

    payload = [texts[i] for i in indices]
    translator = _translator()
    results: dict[int, str] = {}

    for start in range(0, len(payload), CHUNK_SIZE):
        chunk = payload[start : start + CHUNK_SIZE]
        chunk_indices = indices[start : start + CHUNK_SIZE]
        res = translator.translate_text(chunk, source_lang=source_lang, target_lang=target_lang)
        # Single string → single TextResult; list → list of TextResult.
        items = res if isinstance(res, list) else [res]
        for idx, item in zip(chunk_indices, items, strict=True):
            results[idx] = item.text

    return [results.get(i) for i in range(len(texts))]
