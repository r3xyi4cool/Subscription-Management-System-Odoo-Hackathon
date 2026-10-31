import os
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from backend.app.config import config_by_name
from backend.app.extensions import db, migrate, jwt, cors, scheduler
from backend.app.models.auth import TokenBlocklist
from backend.app.utils.errors import APIError, error_response


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_cls = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_cls)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # JWT blocklist callback
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return (
            jsonify({
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Missing or invalid authorization header.",
                    "details": {"info": str(callback)},
                }
            }),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return (
            jsonify({
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Signature verification failed or token is malformed.",
                    "details": {"info": str(callback)},
                }
            }),
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({
                "error": {
                    "code": "TOKEN_EXPIRED",
                    "message": "Token has expired. Please log in again.",
                    "details": {},
                }
            }),
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({
                "error": {
                    "code": "TOKEN_REVOKED",
                    "message": "Token has been revoked. Please log in again.",
                    "details": {},
                }
            }),
            401,
        )

    # Global error handlers
    @app.errorhandler(APIError)
    def handle_api_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        code_name = err.name.upper().replace(" ", "_")
        return (
            jsonify({
                "error": {
                    "code": code_name,
                    "message": err.description,
                    "details": {},
                }
            }),
            err.code,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(err):
        if app.config.get("DEBUG") or app.config.get("TESTING"):
            # In debug/testing, re-raise or print details
            print(f"[UNHANDLED EXCEPTION] {type(err).__name__}: {err}")
        return (
            jsonify({
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred on the server.",
                    "details": {"info": str(err) if app.config.get("DEBUG") else {}},
                }
            }),
            500,
        )

    # Register blueprints
    from backend.app.routes import api_v1, docs_bp

    app.register_blueprint(api_v1)
    app.register_blueprint(docs_bp)

    # Register CLI commands
    from backend.app.cli import register_cli_commands

    register_cli_commands(app)

    # APScheduler initialization (only if enabled and not in testing)
    if app.config.get("ENABLE_SCHEDULER") and not app.config.get("TESTING"):
        from backend.app.jobs.billing_job import scheduled_billing_task

        if not scheduler.running:
            scheduler.add_job(
                func=scheduled_billing_task,
                args=[app],
                trigger="cron",
                hour=0,
                minute=0,
                id="daily_billing_job",
                replace_existing=True,
            )
            scheduler.start()

    return app

