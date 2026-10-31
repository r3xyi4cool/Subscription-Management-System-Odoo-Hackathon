from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    return (
        jsonify({
            "status": "ok",
            "version": "1.0.0",
            "message": "Subscription Management System API is healthy",
        }),
        200,
    )

