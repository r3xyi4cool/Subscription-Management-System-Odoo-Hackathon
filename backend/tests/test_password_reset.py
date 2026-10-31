import os
from datetime import datetime, timedelta, timezone
from backend.app.extensions import db
from backend.app.models.auth import Auth


def test_password_reset_flow(client, app):
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "reset_test@example.com",
            "password": "InitialPass123!",
            "name": "Reset Tester",
        },
    )

    # Request reset
    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset_test@example.com"},
    )
    assert forgot_res.status_code == 200
    token = forgot_res.get_json().get("reset_token")
    if not token and "data" in forgot_res.get_json():
        token = forgot_res.get_json()["data"].get("reset_token")

    assert token is not None

    # Reset password successfully
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewValidPassword123!"},
    )
    assert reset_res.status_code == 200

    # Old password no longer works
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset_test@example.com", "password": "InitialPass123!"},
    )
    assert old_login.status_code == 401

    # New password works
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset_test@example.com", "password": "NewValidPassword123!"},
    )
    assert new_login.status_code == 200

    # Token cannot be reused
    reused_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "AnotherPassword123!"},
    )
    assert reused_res.status_code in (400, 422)


def test_expired_token_rejected(client, app):
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "expired_test@example.com",
            "password": "InitialPass123!",
            "name": "Expired Tester",
        },
    )

    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "expired_test@example.com"},
    )
    token = forgot_res.get_json().get("reset_token")

    # Manually expire the token in the DB
    with app.app_context():
        user = Auth.query.filter_by(email="expired_test@example.com").first()
        user.reset_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.session.commit()

    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewValidPassword123!"},
    )
    assert reset_res.status_code in (400, 422)

