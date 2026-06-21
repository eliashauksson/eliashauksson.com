import math
import re
import time
from collections import Counter
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    session,
)

from .content_loader import get_entry, has_visible_entries, load_entries
from .disposable_domains import is_disposable_email
from .extensions import limiter
from .markdown_utils import render_markdown
from .mail_utils import send_contact_message
from .spam_logging import log_spam
from .translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations

bp = Blueprint("routes", __name__)

PAGES = {"home", "about", "contact", "projects", "logbook"}
MIN_SECONDS_TO_SUBMIT = 3
MAX_EMAIL_LENGTH = 254
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 100
MIN_MESSAGE_LENGTH = 10
MAX_MESSAGE_LENGTH = 5000
LOW_ENTROPY_MIN_LENGTH = 80
LOW_ENTROPY_THRESHOLD = 1.6
REPEATED_CHAR_RE = re.compile(r"([^\s])\1{5,}")


def current_lang() -> str:
    return "de" if request.path == "/de" or request.path.startswith("/de/") else DEFAULT_LANG


def current_page() -> str:
    endpoint = request.endpoint.rsplit(".", 1)[-1] if request.endpoint else ""
    if endpoint == "project_detail":
        return "projects"
    if endpoint == "logbook_detail":
        return "logbook"
    return endpoint if endpoint in PAGES else ""


def validate_lang(lang: str) -> str:
    if lang not in SUPPORTED_LANGS:
        abort(404)
    return lang


def localized_url(page: str, lang: str | None = None, slug: str | None = None) -> str:
    lang = validate_lang(lang or current_lang())
    path = "/home" if page == "home" else f"/{page}"
    if slug and page in {"projects", "logbook"}:
        path = f"{path}/{slug}"
    return path if lang == DEFAULT_LANG else f"/{lang}{path}"


def language_switch_url(lang: str) -> str:
    endpoint = request.endpoint.rsplit(".", 1)[-1] if request.endpoint else ""
    slug = (request.view_args or {}).get("slug")
    if endpoint == "project_detail":
        return localized_url("projects", lang, slug)
    if endpoint == "logbook_detail":
        return localized_url("logbook", lang, slug)
    return localized_url(current_page() or "home", lang)


def load_markdown_content(lang: str, name: str) -> str:
    content_dir = Path(current_app.static_folder) / "content"
    candidates = (content_dir / lang / name, content_dir / DEFAULT_LANG / name)

    for candidate in candidates:
        try:
            return render_markdown(candidate.read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
    return ""


def hidden_trap_triggered() -> bool:
    hidden_values = (
        request.form.get("company") or "",
        request.form.get("website") or "",
        request.form.get("contact_confirm") or "",
    )
    return any(value.strip() for value in hidden_values)


def submitted_too_fast() -> bool:
    started = session.get("contact_started")
    if not isinstance(started, (int, float)):
        return False

    return time.time() - started < MIN_SECONDS_TO_SUBMIT


def structural_spam_reason(form: dict[str, str]) -> str | None:
    name_length = len(form["name"])
    email_length = len(form["email"])
    message_length = len(form["message"])

    if name_length < MIN_NAME_LENGTH or name_length > MAX_NAME_LENGTH:
        return "invalid_name_length"
    if email_length > MAX_EMAIL_LENGTH:
        return "invalid_email_length"
    if message_length < MIN_MESSAGE_LENGTH or message_length > MAX_MESSAGE_LENGTH:
        return "invalid_message_length"
    if REPEATED_CHAR_RE.search(form["message"]):
        return "repeated_characters"
    if has_extremely_low_entropy(form["message"]):
        return "low_entropy"
    if is_disposable_email(form["email"]):
        return "disposable_email"

    return None


def has_extremely_low_entropy(message: str) -> bool:
    compact = "".join(char.lower() for char in message if not char.isspace())
    if len(compact) < LOW_ENTROPY_MIN_LENGTH:
        return False

    counts = Counter(compact)
    length = len(compact)
    entropy = -sum(
        (count / length) * math.log2(count / length) for count in counts.values()
    )
    return entropy < LOW_ENTROPY_THRESHOLD


def block_contact_submission(reason: str, email: str, translations: dict[str, str]) -> str:
    log_spam(reason, email)
    return translations["contact_send_error"]


@bp.app_context_processor
def inject_language_context():
    lang = current_lang()
    return {
        "lang": lang,
        "text": get_translations(lang),
        "current_page": current_page(),
        "localized_url": localized_url,
        "language_switch_url": language_switch_url,
        "has_projects": has_visible_entries("projects", lang),
        "has_logbook": has_visible_entries("logbook", lang),
    }


@bp.route("/")
def main():
    return redirect("/home")


@bp.route("/de")
@bp.route("/de/")
def main_de():
    return redirect("/de/home")


@bp.route("/home", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/home", defaults={"lang": "de"})
def home(lang):
    validate_lang(lang)
    return render_template("home.html")


@bp.route("/about", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/about", defaults={"lang": "de"})
def about(lang):
    lang = validate_lang(lang)
    about_content = load_markdown_content(lang, "about.md")
    return render_template("about.html", about_content=about_content)


@bp.route("/contact", methods=["GET", "POST"], defaults={"lang": DEFAULT_LANG})
@bp.route("/de/contact", methods=["GET", "POST"], defaults={"lang": "de"})
@limiter.limit("5 per hour", methods=["POST"])
@limiter.limit("2 per minute", methods=["POST"])
def contact(lang):
    lang = validate_lang(lang)
    t = get_translations(lang)
    status = None
    error = None
    form = {"name": "", "email": "", "message": ""}

    if request.method == "GET":
        session["contact_started"] = time.time()

    if request.method == "POST":
        form["name"] = (request.form.get("name") or "").strip()
        form["email"] = (request.form.get("email") or "").strip()
        form["message"] = (request.form.get("message") or "").strip()

        if hidden_trap_triggered():
            error = block_contact_submission("honeypot", form["email"], t)
        elif not form["name"] or not form["email"] or not form["message"]:
            error = t["contact_required"]
        elif "@" not in form["email"] or "." not in form["email"].split("@")[-1]:
            error = t["contact_invalid_email"]
        elif submitted_too_fast():
            error = block_contact_submission("too_fast", form["email"], t)
        elif spam_reason := structural_spam_reason(form):
            error = block_contact_submission(spam_reason, form["email"], t)
        else:
            ok, _err = send_contact_message(form["name"], form["email"], form["message"])
            if ok:
                status = t["contact_status"]
                form = {"name": "", "email": "", "message": ""}
            else:
                error = t["contact_send_error"]

    return render_template("contact.html", status=status, error=error, form=form)


@bp.route("/projects", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/projects", defaults={"lang": "de"})
def projects(lang):
    lang = validate_lang(lang)
    project_entries = load_entries("projects", lang)
    return render_template("projects.html", projects=project_entries)


@bp.route("/projects/<slug>", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/projects/<slug>", defaults={"lang": "de"})
def project_detail(lang, slug):
    lang = validate_lang(lang)
    project = get_entry("projects", slug, lang)
    if not project:
        abort(404)
    return render_template("project_detail.html", project=project)


@bp.route("/logbook", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/logbook", defaults={"lang": "de"})
def logbook(lang):
    lang = validate_lang(lang)
    logbook_entries = load_entries("logbook", lang)
    return render_template("logbook.html", entries=logbook_entries)


@bp.route("/logbook/<slug>", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/logbook/<slug>", defaults={"lang": "de"})
def logbook_detail(lang, slug):
    lang = validate_lang(lang)
    entry = get_entry("logbook", slug, lang)
    if not entry:
        abort(404)

    related_project = None
    if entry["related_project"]:
        related_project = get_entry("projects", entry["related_project"], lang)

    return render_template(
        "logbook_detail.html",
        entry=entry,
        related_project=related_project,
    )
