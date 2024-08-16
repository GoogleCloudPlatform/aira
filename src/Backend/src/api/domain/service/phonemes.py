"""
Module containing all phonemize library stuff
"""

from phonemizer import phonemize, separator  # type: ignore[import-untyped]


def phonemize_data_list(data: list[str], language: str = "pt-br") -> list[str]:
    return phonemize(  # type: ignore[no-any-return]
        data,
        language=language,
        backend="espeak",
        separator=separator.Separator(phone=None, word=" ", syllable="|"),
        strip=True,
        preserve_punctuation=True,
    )
