"""Application configuration.

Settings are grouped into classes so the project can switch between
development, testing, and production simply by selecting a config name.
The database defaults to SQLite (zero-setup, ideal for a course project)
but can be pointed at MySQL/PostgreSQL via the DATABASE_URL env variable.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Recommendation engine tunables
    RECOMMENDER_TOP_N = 8          # how many books to recommend on the dashboard
    RECOMMENDER_MIN_OVERLAP = 2    # min co-rated books for two users to be "neighbours"
    RECOMMENDER_NEIGHBOURS = 15    # how many similar users to consider
    RECOMMENDER_METHOD = "cosine"  # "cosine" or "pearson"

    # Seed data location
    SEED_DIR = os.path.join(BASE_DIR, "seed_data")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "library.db")
    )


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    # In-memory database so tests are fast and isolated
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "library.db"))


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
