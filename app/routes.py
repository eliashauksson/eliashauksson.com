import os
from flask import Blueprint, abort, current_app, redirect, render_template, request
from .markdown_utils import render_markdown
from .mail_utils import send_contact_message
from .translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations

bp = Blueprint("routes", __name__)

PAGES = {"home", "about", "contact", "projects"}


def current_lang() -> str:
    return "de" if request.path == "/de" or request.path.startswith("/de/") else DEFAULT_LANG


def current_page() -> str:
    endpoint = request.endpoint.rsplit(".", 1)[-1] if request.endpoint else ""
    return endpoint if endpoint in PAGES else ""


def validate_lang(lang: str) -> str:
    if lang not in SUPPORTED_LANGS:
        abort(404)
    return lang


def localized_url(page: str, lang: str | None = None) -> str:
    lang = validate_lang(lang or current_lang())
    path = "/home" if page == "home" else f"/{page}"
    return path if lang == DEFAULT_LANG else f"/{lang}{path}"


def language_switch_url(lang: str) -> str:
    page = current_page() or "home"
    return localized_url(page, lang)


def load_markdown_content(lang: str, name: str) -> str:
    content_dir = os.path.join(current_app.static_folder, "content")
    path = os.path.join(content_dir, lang, name)
    fallback_path = os.path.join(content_dir, DEFAULT_LANG, name)

    for candidate in (path, fallback_path):
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                return render_markdown(f.read())
        except FileNotFoundError:
            continue
    return ""


@bp.app_context_processor
def inject_language_context():
    lang = current_lang()
    return {
        "lang": lang,
        "text": get_translations(lang),
        "current_page": current_page(),
        "localized_url": localized_url,
        "language_switch_url": language_switch_url,
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
def contact(lang):
    lang = validate_lang(lang)
    t = get_translations(lang)
    status = None
    error = None
    form = {"name": "", "email": "", "message": ""}

    if request.method == "POST":
        form["name"] = (request.form.get("name") or "").strip()
        form["email"] = (request.form.get("email") or "").strip()
        form["message"] = (request.form.get("message") or "").strip()
        honeypot = (request.form.get("company") or "").strip()  # hidden field bots may fill

        # basic validation
        if honeypot:
            error = t["contact_spam"]
        elif not form["name"] or not form["email"] or not form["message"]:
            error = t["contact_required"]
        elif "@" not in form["email"] or "." not in form["email"].split("@")[-1]:
            error = t["contact_invalid_email"]
        else:
            ok, err = send_contact_message(form["name"], form["email"], form["message"])
            if ok:
                status = t["contact_status"]
                form = {"name": "", "email": "", "message": ""}
            else:
                error = err if lang == DEFAULT_LANG and err else t["contact_send_error"]

    return render_template("contact.html", status=status, error=error, form=form)


@bp.route("/projects", defaults={"lang": DEFAULT_LANG})
@bp.route("/de/projects", defaults={"lang": "de"})
def projects(lang):
    validate_lang(lang)
    return render_template("projects.html")
