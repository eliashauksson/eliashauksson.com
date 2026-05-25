import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .env import load_local_env


def create_app() -> Flask:
    """
    Application factory. Creates the Flask app, configures template/static folders,
    registers blueprints and error handlers.
    """
    # Determine absolute paths for templates and static relative to this file
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, ".."))
    load_local_env(project_root)

    templates_path = os.path.join(project_root, "static", "html")
    static_path = os.path.join(project_root, "static")

    app = Flask(__name__, template_folder=templates_path, static_folder=static_path)
    secret_key = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
    if secret_key:
        app.secret_key = secret_key
    else:
        app.secret_key = os.urandom(32)
        app.logger.warning("SECRET_KEY is not set; using an ephemeral session key.")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from .extensions import limiter
    from .spam_logging import configure_spam_logger

    limiter.init_app(app)
    configure_spam_logger(project_root)

    # Register routes
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)

    return app
