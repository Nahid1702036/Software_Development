"""Flask extension instances.

These are created here (un-bound) and initialised against the app inside
the application factory. Keeping them separate avoids circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "info"
