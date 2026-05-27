from __future__ import annotations


def to_latin(text: str, language: str) -> str:
    if language == "ja":
        from app.services.translit import ja

        return ja.to_latin(text)
    from app.services.translit import ru

    return ru.to_latin(text)
