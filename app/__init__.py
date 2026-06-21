import os
from pathlib import Path

from flask import Flask, abort, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .env import load_local_env


def create_app() -> Flask:
    project_root = Path(__file__).parent.parent
    load_local_env(project_root)

    templates_path = project_root / "static" / "html"
    static_path = project_root / "static"

    app = Flask(__name__, template_folder=templates_path, static_folder=static_path)
    is_production = is_production_env()
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=is_production,
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
    )
    secret_key = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
    if secret_key:
        app.secret_key = secret_key
    elif is_production:
        raise RuntimeError("SECRET_KEY is required in production.")
    else:
        app.secret_key = os.urandom(32)
        app.logger.warning("SECRET_KEY is not set; using an ephemeral session key.")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    @app.before_request
    def block_static_templates():
        if request.path.startswith("/static/html/"):
            abort(404)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';",
        )
        if is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    from .extensions import limiter
    from .spam_logging import configure_spam_logger

    limiter.init_app(app)
    configure_spam_logger(project_root)

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    from .errors import register_error_handlers
    register_error_handlers(app)

    return app


def is_production_env() -> bool:
    return os.getenv("FLASK_ENV") == "production" or os.getenv("APP_ENV") == "production"
