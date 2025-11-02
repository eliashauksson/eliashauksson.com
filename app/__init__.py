import os
from flask import Flask


def create_app() -> Flask:
    """
    Application factory. Creates the Flask app, configures template/static folders,
    registers blueprints and error handlers.
    """
    # Determine absolute paths for templates and static relative to this file
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(here, ".."))
    templates_path = os.path.join(project_root, "static", "html")
    static_path = os.path.join(project_root, "static")

    app = Flask(__name__, template_folder=templates_path, static_folder=static_path)

    # Register routes
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)

    return app
