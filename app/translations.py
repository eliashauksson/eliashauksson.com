import json
from functools import lru_cache
from pathlib import Path


DEFAULT_LANG = "en"
SUPPORTED_LANGS = {"en", "de"}


def _translations_dir() -> Path:
    return Path(__file__).parent.parent / "translations"


@lru_cache(maxsize=len(SUPPORTED_LANGS))
def get_translations(lang: str) -> dict[str, str]:
    if lang not in SUPPORTED_LANGS:
        raise KeyError(f"Unsupported language: {lang}")

    path = _translations_dir() / f"{lang}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)
