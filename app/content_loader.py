import re
from datetime import date
from pathlib import Path

from flask import current_app

from .markdown_utils import render_markdown
from .translations import DEFAULT_LANG, SUPPORTED_LANGS


SECTIONS = {"projects", "logbook"}
SLUG_RE = re.compile(r"[^a-zA-Z0-9_-]+")
TRUE_VALUES = {"1", "true", "yes", "on"}


def load_entries(section: str, lang: str) -> list[dict]:
    """
    Load visible markdown entries for a section and language.
    Falls back to English when no visible localized entries exist.
    """
    entries = _load_entries_for_lang(section, lang)
    if lang != DEFAULT_LANG and not entries:
        entries = _load_entries_for_lang(section, DEFAULT_LANG)
    return sorted(entries, key=_sort_key, reverse=True)


def get_entry(section: str, slug: str, lang: str) -> dict | None:
    """Load one visible entry, falling back to English when localized content is missing."""
    slug = _clean_slug(slug)
    for candidate_lang in _candidate_langs(lang):
        for entry in _load_entries_for_lang(section, candidate_lang):
            if entry["slug"] == slug:
                return entry
    return None


def has_visible_entries(section: str, lang: str) -> bool:
    return bool(load_entries(section, lang))


def _load_entries_for_lang(section: str, lang: str) -> list[dict]:
    _validate(section, lang)
    content_dir = _content_root() / section / lang
    if not content_dir.is_dir():
        return []

    entries = []
    for path in sorted(content_dir.glob("*.md")):
        entry = _load_entry(path, section, lang)
        if entry:
            entries.append(entry)
    return entries


def _load_entry(path: Path, section: str, lang: str) -> dict | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        current_app.logger.warning("Could not read content file %s: %s", path, exc)
        return None

    metadata, body = _parse_frontmatter(raw)
    if _is_draft(metadata):
        return None

    slug = _clean_slug(metadata.get("slug") or path.stem)
    if not slug:
        current_app.logger.warning("Skipping content file with empty slug: %s", path)
        return None

    entry_date = _parse_date(metadata.get("date", ""))
    tags = _parse_tags(metadata.get("tags", ""))

    return {
        "section": section,
        "lang": lang,
        "slug": slug,
        "title": metadata.get("title") or _title_from_slug(slug),
        "date": entry_date,
        "date_iso": entry_date.isoformat() if entry_date else "",
        "status": metadata.get("status", ""),
        "summary": metadata.get("summary", ""),
        "tags": tags,
        "cover_image": metadata.get("cover_image", ""),
        "related_project": metadata.get("related_project", ""),
        "html": render_markdown(body.strip()),
        "source_path": str(path),
    }


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, raw

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, raw

    metadata = {}
    for line in lines[1:end_index]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = _strip_quotes(value.strip())

    return metadata, "\n".join(lines[end_index + 1 :])


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        current_app.logger.warning("Invalid content date: %s", value)
        return None


def _parse_tags(value: str) -> list[str]:
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _is_draft(metadata: dict[str, str]) -> bool:
    return metadata.get("draft", "").strip().lower() in TRUE_VALUES


def _clean_slug(value: str) -> str:
    slug = SLUG_RE.sub("-", value.strip()).strip("-")
    return slug.lower()


def _title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def _sort_key(entry: dict) -> tuple[date, str]:
    return (entry["date"] or date.min, entry["slug"])


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _candidate_langs(lang: str) -> list[str]:
    _validate_lang(lang)
    if lang == DEFAULT_LANG:
        return [DEFAULT_LANG]
    return [lang, DEFAULT_LANG]


def _validate(section: str, lang: str) -> None:
    if section not in SECTIONS:
        raise ValueError(f"Unsupported content section: {section}")
    _validate_lang(lang)


def _validate_lang(lang: str) -> None:
    if lang not in SUPPORTED_LANGS:
        raise ValueError(f"Unsupported language: {lang}")


def _content_root() -> Path:
    project_root = Path(current_app.root_path).parent
    return project_root / "content"
