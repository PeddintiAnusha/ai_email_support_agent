import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration for the AI Email Support Agent."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # Database (SQLite for local/dev use)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    # AI / LLM settings
    # If OPENAI_API_KEY is not set, ai_service.py automatically falls back
    # to a rule-based mock so the app is fully runnable without an API key.
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # Pagination
    EMAILS_PER_PAGE = 10

    # Session
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
