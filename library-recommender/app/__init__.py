"""Application factory.

Creating the app inside a function (rather than at import time) lets us spin
up isolated instances for testing and pick a config at runtime. The factory
wires extensions, registers blueprints, attaches the recommendation engine,
and exposes a ``flask seed`` CLI command.
"""
import os

import click
from flask import Flask

from config import config
from app.extensions import db, login_manager
from app.recommender import RecommendationEngine


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_CONFIG", "default")
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # --- extensions -------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    # Models must be imported so SQLAlchemy registers the tables.
    from app.models import User, Book, Rating

    # --- recommendation engine (one per app) ------------------------------
    app.recommender = RecommendationEngine(db, Rating, Book, app.config)

    # --- blueprints -------------------------------------------------------
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # --- template helpers -------------------------------------------------
    @app.context_processor
    def inject_helpers():
        def star_string(score):
            full = int(round(score))
            return "\u2605" * full + "\u2606" * (5 - full)
        return dict(star_string=star_string)

    # --- CLI commands -----------------------------------------------------
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Drop and recreate all tables first.")
    def seed(reset):
        """Load the sample dataset from seed_data/*.csv."""
        from app.seed import seed_database
        with app.app_context():
            counts = seed_database(app.config["SEED_DIR"], reset=reset)
            app.recommender.invalidate()
        click.echo(f"Seeded: {counts['books']} books, "
                   f"{counts['users']} users, {counts['ratings']} ratings.")

    return app
