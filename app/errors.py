from flask import render_template, request

from .spam_logging import log_spam
from .translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations


def _request_lang() -> str:
    lang = "de" if request.path == "/de" or request.path.startswith("/de/") else DEFAULT_LANG
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def _contact_form_from_request() -> dict[str, str]:
    return {
        "name": (request.form.get("name") or "").strip(),
        "email": (request.form.get("email") or "").strip(),
        "message": (request.form.get("message") or "").strip(),
    }


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("403.html"), 403

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        form = _contact_form_from_request()
        log_spam("rate_limit", form["email"])

        if request.path.rstrip("/").endswith("/contact"):
            t = get_translations(_request_lang())
            return (
                render_template(
                    "contact.html",
                    status=None,
                    error=t["contact_send_error"],
                    form=form,
                ),
                429,
            )

        return render_template("500.html"), 429
