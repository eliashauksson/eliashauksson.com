import hmac
import os
import re
import secrets
import shutil
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename

from .content_loader import _parse_frontmatter, _parse_tags, load_entries
from .extensions import limiter
from .markdown_utils import render_markdown


bp = Blueprint("admin", __name__, url_prefix="/admin")

ADMIN_LANG = "en"
SECTIONS = {
    "projects": {
        "label": "Projects",
        "single": "project",
        "public_page": "routes.project_detail",
    },
    "logbook": {
        "label": "Logbook",
        "single": "logbook entry",
        "public_page": "routes.logbook_detail",
    },
}
ALLOWED_MEDIA_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
FILENAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*\.md$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TRUE_VALUES = {"1", "true", "yes", "on"}


@bp.before_request
def protect_admin():
    if not admin_enabled():
        abort(404)

    if request.method == "POST" and not validate_csrf_token():
        abort(403)


@bp.context_processor
def inject_admin_context():
    return {
        "admin_csrf_token": csrf_token,
        "admin_sections": SECTIONS,
        "admin_authenticated": is_admin_authenticated(),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin_authenticated():
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_enabled() -> bool:
    return bool(os.getenv("ADMIN_PASSWORD"))


def is_admin_authenticated() -> bool:
    return session.get("admin_authenticated") is True


def csrf_token() -> str:
    token = session.get("admin_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["admin_csrf_token"] = token
    return token


def validate_csrf_token() -> bool:
    expected = session.get("admin_csrf_token")
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


@bp.route("")
@bp.route("/")
@login_required
def dashboard():
    project_entries = load_entries("projects", ADMIN_LANG)
    logbook_entries = load_entries("logbook", ADMIN_LANG)
    latest_entries = sorted(
        [*project_entries, *logbook_entries],
        key=lambda entry: (entry["date"] or date.min, entry["slug"]),
        reverse=True,
    )[:6]

    return render_template(
        "admin/dashboard.html",
        project_count=len(project_entries),
        logbook_count=len(logbook_entries),
        latest_entries=latest_entries,
    )


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour", methods=["POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if is_admin_authenticated():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        password = request.form.get("password") or ""
        if hmac.compare_digest(password, os.getenv("ADMIN_PASSWORD", "")):
            session["admin_authenticated"] = True
            session.pop("admin_csrf_token", None)
            flash("Signed in.", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/admin"):
                return redirect(next_url)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid password.", "error")

    return render_template("admin/login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.pop("admin_authenticated", None)
    session.pop("admin_csrf_token", None)
    flash("Signed out.", "success")
    return redirect(url_for("admin.login"))


@bp.route("/projects")
@login_required
def projects():
    return render_admin_list("projects")


@bp.route("/logbook")
@login_required
def logbook():
    return render_admin_list("logbook")


@bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():
    return edit_content("projects")


@bp.route("/logbook/new", methods=["GET", "POST"])
@login_required
def new_logbook():
    return edit_content("logbook")


@bp.route("/projects/edit/<filename>", methods=["GET", "POST"])
@login_required
def edit_project(filename):
    return edit_content("projects", filename)


@bp.route("/logbook/edit/<filename>", methods=["GET", "POST"])
@login_required
def edit_logbook(filename):
    return edit_content("logbook", filename)


@bp.route("/projects/delete/<filename>", methods=["GET", "POST"])
@login_required
def delete_project(filename):
    return delete_content("projects", filename)


@bp.route("/logbook/delete/<filename>", methods=["GET", "POST"])
@login_required
def delete_logbook(filename):
    return delete_content("logbook", filename)


@bp.route("/media")
@login_required
def media():
    return render_template(
        "admin/media.html",
        uploaded_path=request.args.get("uploaded_path", ""),
        media_files=list_media_files(),
        max_upload_mb=MAX_UPLOAD_BYTES // (1024 * 1024),
    )


@bp.route("/media/upload", methods=["POST"])
@login_required
def upload_media():
    section = request.form.get("section", "")
    slug = request.form.get("slug", "")
    file = request.files.get("file")

    if section not in SECTIONS:
        flash("Choose a valid media section.", "error")
        return redirect(url_for("admin.media"))
    if not validate_slug(slug):
        flash("Use a lowercase slug with letters, numbers, and hyphens only.", "error")
        return redirect(url_for("admin.media"))
    if not file or not file.filename:
        flash("Choose an image to upload.", "error")
        return redirect(url_for("admin.media"))

    filename = secure_filename(file.filename).lower()
    if not allowed_media_filename(filename):
        flash("Unsupported file type.", "error")
        return redirect(url_for("admin.media"))

    upload_dir = media_dir(section, slug)
    upload_dir.mkdir(parents=True, exist_ok=True)
    final_filename = unique_filename(upload_dir, filename)
    destination = upload_dir / final_filename
    file.save(destination)

    uploaded_path = f"/static/img/{section}/{slug}/{final_filename}"
    flash("Image uploaded.", "success")
    return redirect(url_for("admin.media", uploaded_path=uploaded_path))


def render_admin_list(section: str):
    entries = list_admin_entries(section)
    return render_template(
        "admin/list.html",
        section=section,
        section_config=SECTIONS[section],
        entries=entries,
    )


def edit_content(section: str, filename: str | None = None):
    is_new = filename is None
    entry = empty_form(section)

    if not is_new:
        entry = load_admin_file(section, filename)

    if request.method == "POST":
        entry = form_to_entry(section)
        errors = validate_entry(section, entry)
        preview_html = render_markdown(entry["body"])

        if request.form.get("action") == "preview":
            return render_template(
                "admin/edit.html",
                section=section,
                section_config=SECTIONS[section],
                entry=entry,
                filename=filename,
                is_new=is_new,
                errors=errors,
                preview_html=preview_html,
            )

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "admin/edit.html",
                section=section,
                section_config=SECTIONS[section],
                entry=entry,
                filename=filename,
                is_new=is_new,
                errors=errors,
                preview_html=preview_html,
            )

        if is_new:
            target_filename = generated_filename(entry)
            target_path = content_path(section, target_filename, must_exist=False)
            if target_path.exists():
                flash("A file with that generated filename already exists.", "error")
                return render_template(
                    "admin/edit.html",
                    section=section,
                    section_config=SECTIONS[section],
                    entry=entry,
                    filename=target_filename,
                    is_new=is_new,
                    errors=[],
                    preview_html=preview_html,
                )
            filename = target_filename
        else:
            target_path = content_path(section, filename)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(build_markdown(section, entry), encoding="utf-8")
        flash("Content saved.", "success")
        return redirect(url_for(f"admin.{section}"))

    return render_template(
        "admin/edit.html",
        section=section,
        section_config=SECTIONS[section],
        entry=entry,
        filename=filename,
        is_new=is_new,
        errors=[],
        preview_html="",
    )


def delete_content(section: str, filename: str):
    entry = load_admin_file(section, filename)

    if request.method == "POST":
        source = content_path(section, filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        trash = trash_dir(section)
        trash.mkdir(parents=True, exist_ok=True)
        destination = trash / f"{timestamp}-{filename}"
        shutil.move(str(source), destination)
        flash("Content moved to trash.", "success")
        return redirect(url_for(f"admin.{section}"))

    return render_template(
        "admin/delete_confirm.html",
        section=section,
        section_config=SECTIONS[section],
        filename=filename,
        entry=entry,
    )


def list_admin_entries(section: str) -> list[dict]:
    entries = []
    directory = content_dir(section)
    if not directory.is_dir():
        return entries

    for path in sorted(directory.glob("*.md")):
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            current_app.logger.warning("Could not read admin content file %s: %s", path, exc)
            continue
        metadata, body = _parse_frontmatter(raw)
        slug = metadata.get("slug") or path.stem
        entry = {
            "filename": path.name,
            "title": metadata.get("title") or title_from_slug(slug),
            "slug": slug,
            "date": metadata.get("date", ""),
            "draft": is_truthy(metadata.get("draft", "")),
            "lang": ADMIN_LANG,
            "status": metadata.get("status", ""),
            "summary": metadata.get("summary", ""),
            "body": body,
        }
        if not entry["draft"] and validate_slug(slug):
            entry["public_url"] = url_for(SECTIONS[section]["public_page"], slug=slug)
        else:
            entry["public_url"] = ""
        entries.append(entry)

    return sorted(entries, key=lambda item: (item["date"], item["filename"]), reverse=True)


def load_admin_file(section: str, filename: str) -> dict:
    path = content_path(section, filename)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        abort(404)

    metadata, body = _parse_frontmatter(raw)
    entry = empty_form(section)
    entry.update(
        {
            "title": metadata.get("title", ""),
            "slug": metadata.get("slug", ""),
            "date": metadata.get("date", ""),
            "status": metadata.get("status", ""),
            "related_project": metadata.get("related_project", ""),
            "summary": metadata.get("summary", ""),
            "tags": metadata.get("tags", ""),
            "cover_image": metadata.get("cover_image", ""),
            "draft": is_truthy(metadata.get("draft", "")),
            "body": body.strip(),
        }
    )
    return entry


def form_to_entry(section: str) -> dict:
    return {
        "title": clean_line(request.form.get("title", "")),
        "slug": clean_line(request.form.get("slug", "")),
        "date": clean_line(request.form.get("date", "")),
        "status": clean_line(request.form.get("status", "")),
        "related_project": clean_line(request.form.get("related_project", "")),
        "summary": clean_line(request.form.get("summary", "")),
        "tags": clean_line(request.form.get("tags", "")),
        "cover_image": clean_line(request.form.get("cover_image", "")),
        "draft": request.form.get("draft") == "on",
        "body": request.form.get("body", ""),
    }


def empty_form(section: str) -> dict:
    today = date.today().isoformat()
    return {
        "title": "",
        "slug": "",
        "date": today,
        "status": "",
        "related_project": "",
        "summary": "",
        "tags": "",
        "cover_image": "",
        "draft": False,
        "body": "",
    }


def validate_entry(section: str, entry: dict) -> list[str]:
    errors = []
    if not entry["title"]:
        errors.append("Title is required.")
    if not valid_date(entry["date"]):
        errors.append("Date must use YYYY-MM-DD.")

    slug = entry["slug"]
    if slug and not validate_slug(slug):
        errors.append("Slug must use lowercase letters, numbers, and hyphens only.")
    if section == "projects" and not slug:
        errors.append("Project slug is required.")
    if entry["related_project"] and not validate_slug(entry["related_project"]):
        errors.append("Related project must be a valid slug.")
    if entry["cover_image"] and not entry["cover_image"].startswith("/static/img/"):
        errors.append("Cover image must start with /static/img/.")
    if len(entry["body"]) > 200_000:
        errors.append("Markdown body is too large.")
    _parse_tags(entry["tags"])
    return errors


def build_markdown(section: str, entry: dict) -> str:
    fields = [
        ("title", entry["title"]),
        ("slug", entry["slug"]),
        ("date", entry["date"]),
    ]
    if section == "projects":
        fields.append(("status", entry["status"]))
    else:
        fields.append(("related_project", entry["related_project"]))
    fields.extend(
        [
            ("summary", entry["summary"]),
            ("tags", entry["tags"]),
            ("cover_image", entry["cover_image"]),
            ("draft", "true" if entry["draft"] else "false"),
        ]
    )

    lines = ["---"]
    for key, value in fields:
        if key == "slug" and section == "logbook" and not value:
            continue
        lines.append(f"{key}: {frontmatter_value(value)}")
    lines.extend(["---", "", entry["body"].strip(), ""])
    return "\n".join(lines)


def generated_filename(entry: dict) -> str:
    slug = entry["slug"] or slugify(entry["title"])
    return f"{entry['date']}-{slug}.md"


def content_path(section: str, filename: str, must_exist: bool = True) -> Path:
    if section not in SECTIONS:
        abort(404)
    if not validate_markdown_filename(filename):
        abort(404)

    directory = content_dir(section)
    joined = safe_join(str(directory), filename)
    if not joined:
        abort(404)
    path = Path(joined).resolve()
    if path.parent != directory.resolve():
        abort(404)
    if must_exist and not path.is_file():
        abort(404)
    return path


def content_dir(section: str) -> Path:
    return project_root() / "content" / section / ADMIN_LANG


def trash_dir(section: str) -> Path:
    return project_root() / "content" / ".trash" / section


def media_dir(section: str, slug: str) -> Path:
    return project_root() / "static" / "img" / section / slug


def project_root() -> Path:
    return Path(current_app.root_path).parent


def list_media_files() -> list[dict]:
    root = project_root() / "static" / "img"
    files = []
    for section in SECTIONS:
        section_root = root / section
        if not section_root.is_dir():
            continue
        for path in sorted(section_root.glob("*/*")):
            if path.is_file() and allowed_media_filename(path.name):
                files.append(
                    {
                        "name": path.name,
                        "path": f"/static/img/{section}/{path.parent.name}/{path.name}",
                        "section": section,
                        "slug": path.parent.name,
                    }
                )
    return files


def allowed_media_filename(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_MEDIA_EXTENSIONS


def unique_filename(directory: Path, filename: str) -> str:
    stem, suffix = Path(filename).stem, Path(filename).suffix
    candidate = filename
    counter = 2
    while (directory / candidate).exists():
        candidate = f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


def validate_markdown_filename(filename: str) -> bool:
    return bool(FILENAME_RE.fullmatch(filename)) and secure_filename(filename) == filename


def validate_slug(slug: str) -> bool:
    return bool(SLUG_RE.fullmatch(slug))


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def is_truthy(value: str) -> bool:
    return value.strip().lower() in TRUE_VALUES


def clean_line(value: str) -> str:
    return " ".join((value or "").splitlines()).strip()


def frontmatter_value(value: str) -> str:
    return clean_line(value).replace("---", "- - -")
