from flask import render_template


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
