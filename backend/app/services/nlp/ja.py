"""Japanese tokenization + lemmatization (SudachiPy).

SudachiPy returns morphemes with surface / dictionary_form / 6-tuple POS
/ katakana reading. We expose hiragana readings for the furigana ruby
in the UI, mapped via the 0x60 katakana→hiragana offset.
"""

from __future__ import annotations

from functools import lru_cache

from app.services.nlp.types import AnalyzedToken

# pos[0] (top-level category in SudachiPy's UniDic tagset) → kaikki POS.
# Used downstream by ``services.dictionary`` so JA lookups land on the
# right Wiktionary row.
_TOP_POS_TO_KAIKKI: dict[str, tuple[str, ...]] = {
    "名詞": ("noun", "pron", "name"),
    "代名詞": ("pron",),
    "動詞": ("verb",),
    "形容詞": ("adj",),
    "形状詞": ("adj",),
    "副詞": ("adv",),
    "助動詞": ("aux",),
    "助詞": ("prt", "particle"),
    "接続詞": ("conj",),
    "感動詞": ("intj",),
    "接頭辞": ("prefix",),
    "接尾辞": ("suffix",),
    "連体詞": ("adj",),
}

# 補助記号 = supplementary symbols (punctuation, brackets, etc.).
_NON_WORD_TOP = {"補助記号", "記号", "空白"}


@lru_cache(maxsize=1)
def _tokenizer_and_mode():
    from sudachipy import dictionary, tokenizer

    tok = dictionary.Dictionary(dict="full").create()
    return tok, tokenizer.Tokenizer.SplitMode.C


def _katakana_to_hiragana(s: str) -> str:
    out_chars: list[str] = []
    for c in s:
        # Standard katakana range U+30A1 (ァ) – U+30F6 (ヶ).
        if "ァ" <= c <= "ヶ":
            out_chars.append(chr(ord(c) - 0x60))
        else:
            out_chars.append(c)
    return "".join(out_chars)


def _normalize_top_pos(pos_tuple: tuple[str, ...]) -> str | None:
    return pos_tuple[0] if pos_tuple else None


def analyze_line(text: str) -> list[AnalyzedToken]:
    if not text.strip():
        return []
    tok, mode = _tokenizer_and_mode()
    out: list[AnalyzedToken] = []
    for m in tok.tokenize(text, mode):
        surface = m.surface()
        pos_tuple = m.part_of_speech()
        top = _normalize_top_pos(pos_tuple)

        if top in _NON_WORD_TOP or not surface.strip():
            out.append(
                AnalyzedToken(
                    surface=surface,
                    lemma=surface,
                    pos=None,
                    grammar=None,
                    is_word=False,
                    reading=None,
                )
            )
            continue

        reading_kata = m.reading_form() or ""
        reading_hira = _katakana_to_hiragana(reading_kata) if reading_kata else None
        # Suppress the reading when it's just the surface (kana-only tokens).
        if reading_hira and reading_hira == surface:
            reading_hira = None

        out.append(
            AnalyzedToken(
                surface=surface,
                lemma=m.dictionary_form() or surface,
                pos=top,
                grammar=",".join(p for p in pos_tuple if p and p != "*"),
                is_word=True,
                reading=reading_hira,
            )
        )
    return out


# Map the SudachiPy top-level POS to the candidate list the dictionary
# layer should try. Exposed here (rather than in ``dictionary.py``) so
# the language layer stays the single source of truth on POS mapping.
def candidate_kaikki_pos(top_pos: str | None) -> tuple[str, ...]:
    if not top_pos:
        return ()
    return _TOP_POS_TO_KAIKKI.get(top_pos, ())
