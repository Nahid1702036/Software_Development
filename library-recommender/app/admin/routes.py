"""Admin blueprint: book management plus library analytics.

Every view is guarded by ``admin_required`` which 403s non-admin users.
"""
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import Book, Rating, User

admin_bp = Blueprint("admin", __name__)


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route("/")
@admin_required
def index():
    stats = {
        "books": Book.query.count(),
        "users": User.query.count(),
        "ratings": Rating.query.count(),
        "reviews": Rating.query.filter(Rating.review != "").count(),
    }

    # Most-rated books (by count)
    most_rated = (
        db.session.query(Book, func.count(Rating.id).label("n"))
        .join(Rating).group_by(Book.id)
        .order_by(func.count(Rating.id).desc()).limit(5).all()
    )
    # Highest-rated books with at least 3 votes
    highest = (
        db.session.query(Book, func.avg(Rating.score).label("avg"),
                         func.count(Rating.id).label("n"))
        .join(Rating).group_by(Book.id)
        .having(func.count(Rating.id) >= 3)
        .order_by(func.avg(Rating.score).desc()).limit(5).all()
    )
    # Ratings distribution 1..5 for the bar chart
    dist = {i: 0 for i in range(1, 6)}
    for score, n in (db.session.query(Rating.score, func.count(Rating.id))
                     .group_by(Rating.score).all()):
        dist[score] = n

    return render_template(
        "admin/dashboard.html", stats=stats,
        most_rated=most_rated, highest=highest, dist=dist,
    )


@admin_bp.route("/books")
@admin_required
def books():
    all_books = Book.query.order_by(Book.title).all()
    return render_template("admin/books.html", books=all_books)


@admin_bp.route("/books/new", methods=["GET", "POST"])
@admin_required
def new_book():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        author = (request.form.get("author") or "").strip()
        if not title or not author:
            flash("Title and author are required.", "error")
            return render_template("admin/book_form.html", book=None, form=request.form)
        book = Book(
            title=title, author=author,
            genre=(request.form.get("genre") or "").strip(),
            year=int(request.form["year"]) if request.form.get("year") else None,
            isbn=(request.form.get("isbn") or "").strip(),
            description=(request.form.get("description") or "").strip(),
            cover_color=(request.form.get("cover_color") or "#7c2d2d"),
        )
        db.session.add(book)
        db.session.commit()
        current_app.recommender.invalidate()
        flash(f"Added \u201c{book.title}\u201d.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", book=None, form={})


@admin_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    if request.method == "POST":
        book.title = (request.form.get("title") or book.title).strip()
        book.author = (request.form.get("author") or book.author).strip()
        book.genre = (request.form.get("genre") or "").strip()
        book.year = int(request.form["year"]) if request.form.get("year") else None
        book.isbn = (request.form.get("isbn") or "").strip()
        book.description = (request.form.get("description") or "").strip()
        book.cover_color = request.form.get("cover_color") or book.cover_color
        db.session.commit()
        flash("Book updated.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", book=book, form={})


@admin_bp.route("/books/<int:book_id>/delete", methods=["POST"])
@admin_required
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    db.session.delete(book)
    db.session.commit()
    current_app.recommender.invalidate()
    flash("Book deleted.", "info")
    return redirect(url_for("admin.books"))
