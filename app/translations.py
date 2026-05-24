import json
import os
from functools import lru_cache
from typing import Dict


DEFAULT_LANG = "en"
SUPPORTED_LANGS = {"en", "de"}


def _translations_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, ".."))
    return os.path.join(project_root, "translations")


@lru_cache(maxsize=len(SUPPORTED_LANGS))
def get_translations(lang: str) -> Dict[str, str]:
    if lang not in SUPPORTED_LANGS:
        raise KeyError(f"Unsupported language: {lang}")

    path = os.path.join(_translations_dir(), f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
