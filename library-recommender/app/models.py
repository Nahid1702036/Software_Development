"""Domain models for the recommendation engine.

The data model is deliberately small and well-normalised:

    User  1 ──< Rating >── 1  Book

A Rating is the join entity carrying the score (1-5) and an optional
text review. A composite unique constraint guarantees a user can rate
a given book at most once (re-rating updates the existing row).
"""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    bio = db.Column(db.String(280), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ratings = db.relationship(
        "Rating", back_populates="user", cascade="all, delete-orphan"
    )

    # --- password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # --- convenience ------------------------------------------------------
    @property
    def rated_book_ids(self) -> set:
        return {r.book_id for r in self.ratings}

    def __repr__(self):
        return f"<User {self.id} {self.email}>"


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False, index=True)
    genre = db.Column(db.String(80), index=True)
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(20))
    description = db.Column(db.Text, default="")
    cover_color = db.Column(db.String(7), default="#7c2d2d")  # for the spine UI

    ratings = db.relationship(
        "Rating", back_populates="book", cascade="all, delete-orphan"
    )

    # --- aggregate helpers ------------------------------------------------
    @property
    def average_rating(self) -> float:
        scores = [r.score for r in self.ratings]
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    @property
    def rating_count(self) -> int:
        return len(self.ratings)

    @property
    def reviews(self):
        """Ratings that carry a non-empty text review, newest first."""
        return sorted(
            [r for r in self.ratings if r.review],
            key=lambda r: r.created_at,
            reverse=True,
        )

    def __repr__(self):
        return f"<Book {self.id} {self.title!r}>"


class Rating(db.Model):
    __tablename__ = "ratings"
    __table_args__ = (
        db.UniqueConstraint("user_id", "book_id", name="uq_user_book"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)  # 1..5
    review = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="ratings")
    book = db.relationship("Book", back_populates="ratings")

    def __repr__(self):
        return f"<Rating u{self.user_id} b{self.book_id} = {self.score}>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
