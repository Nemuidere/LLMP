from transliterate import translit


def to_latin(text: str) -> str:
    """Transliterate Russian Cyrillic → Latin (``reversed=True`` means cyr→lat)."""
    if not text:
        return ""
    return translit(text, "ru", reversed=True)
