import os
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_curr_dir)
_root_dir = os.path.dirname(_backend_dir)
for _env_candidate in [os.path.join(_root_dir, ".env"), os.path.join(_backend_dir, ".env")]:
    if os.path.exists(_env_candidate):
        load_dotenv(_env_candidate)
load_dotenv()

BASE_DIR = _backend_dir


def fix_database_url(url: str) -> str:
    if not url:
        return "sqlite:///subscription_system.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-default-12345")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-default-12345")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    SQLALCHEMY_DATABASE_URI = fix_database_url(os.getenv("DATABASE_URL", ""))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@12345")

    MAIL_BACKEND = os.getenv("MAIL_BACKEND", "dev")
    MAIL_OUTBOX_DIR = os.getenv(
        "MAIL_OUTBOX_DIR", os.path.join(BASE_DIR, "outbox")
    )
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "false").lower() in (
        "true",
        "1",
        "yes",
    )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    ENABLE_SCHEDULER = False
    MAIL_BACKEND = "dev"


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

