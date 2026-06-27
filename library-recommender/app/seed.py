"""Load the sample CSV dataset into the database.

Invoked via the ``flask seed`` CLI command (registered in the app factory).
Idempotent: running it twice will not create duplicate books or users.
An admin account is always created so the admin panel can be explored.
"""
import csv
import os

from app.extensions import db
from app.models import User, Book, Rating


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed_database(seed_dir, reset=False):
    if reset:
        db.drop_all()
        db.create_all()

    books_by_isbn = {}
    users_by_email = {}

    # --- books ------------------------------------------------------------
    for row in _read_csv(os.path.join(seed_dir, "books.csv")):
        book = Book.query.filter_by(isbn=row["isbn"]).first()
        if not book:
            book = Book(
                title=row["title"],
                author=row["author"],
                genre=row["genre"],
                year=int(row["year"]) if row["year"] else None,
                isbn=row["isbn"],
                cover_color=row.get("cover_color") or "#7c2d2d",
                description=row.get("description", ""),
            )
            db.session.add(book)
        books_by_isbn[row["isbn"]] = book
    db.session.flush()

    # --- admin account ----------------------------------------------------
    admin = User.query.filter_by(email="admin@library.dev").first()
    if not admin:
        admin = User(name="Library Admin", email="admin@library.dev",
                     is_admin=True, bio="Keeper of the stacks.")
        admin.set_password("admin123")
        db.session.add(admin)

    # --- users ------------------------------------------------------------
    for row in _read_csv(os.path.join(seed_dir, "users.csv")):
        user = User.query.filter_by(email=row["email"]).first()
        if not user:
            user = User(name=row["name"], email=row["email"], bio=row.get("bio", ""))
            user.set_password(row["password"])
            db.session.add(user)
        users_by_email[row["email"]] = user
    db.session.flush()

    # --- ratings ----------------------------------------------------------
    for row in _read_csv(os.path.join(seed_dir, "ratings.csv")):
        user = users_by_email.get(row["user_email"])
        book = books_by_isbn.get(row["book_isbn"])
        if not user or not book:
            continue
        existing = Rating.query.filter_by(user_id=user.id, book_id=book.id).first()
        if existing:
            continue
        db.session.add(Rating(
            user_id=user.id,
            book_id=book.id,
            score=int(row["score"]),
            review=row.get("review", ""),
        ))

    db.session.commit()
    return {
        "books": Book.query.count(),
        "users": User.query.count(),
        "ratings": Rating.query.count(),
    }
