"""Main blueprint: dashboard, catalog browsing, book detail, rating, profile."""
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, abort,
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import Book, Rating

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    engine = current_app.recommender
    recs = engine.recommend_for(current_user.id)

    # Hydrate recommendation book objects for the template
    rec_cards = []
    for r in recs:
        book = db.session.get(Book, r.book_id)
        if book:
            rec_cards.append({"book": book, "rec": r})

    my_ratings = (
        Rating.query.filter_by(user_id=current_user.id)
        .order_by(Rating.created_at.desc())
        .all()
    )
    is_cold_start = bool(recs) and recs[0].method == "popularity"

    return render_template(
        "dashboard.html",
        rec_cards=rec_cards,
        my_ratings=my_ratings,
        is_cold_start=is_cold_start,
        method=engine.method,
    )


@main_bp.route("/books")
@login_required
def books():
    q = (request.args.get("q") or "").strip()
    genre = (request.args.get("genre") or "").strip()
    sort = request.args.get("sort", "title")

    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Book.title.ilike(like), Book.author.ilike(like)))
    if genre:
        query = query.filter(Book.genre == genre)

    all_books = query.all()

    if sort == "rating":
        all_books.sort(key=lambda b: b.average_rating, reverse=True)
    elif sort == "popular":
        all_books.sort(key=lambda b: b.rating_count, reverse=True)
    elif sort == "year":
        all_books.sort(key=lambda b: b.year or 0, reverse=True)
    else:
        all_books.sort(key=lambda b: b.title.lower())

    genres = [g[0] for g in db.session.query(Book.genre).distinct().order_by(Book.genre)]
    my_scores = {r.book_id: r.score for r in current_user.ratings}

    return render_template(
        "books.html",
        books=all_books, genres=genres, q=q,
        active_genre=genre, sort=sort, my_scores=my_scores,
    )


@main_bp.route("/book/<int:book_id>")
@login_required
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    my_rating = Rating.query.filter_by(
        user_id=current_user.id, book_id=book_id
    ).first()
    # "Readers also enjoyed": other books rated highly by people who liked this one
    fans = [r.user_id for r in book.ratings if r.score >= 4]
    also = (
        db.session.query(Book, func.avg(Rating.score).label("avg"),
                         func.count(Rating.id).label("n"))
        .join(Rating, Rating.book_id == Book.id)
        .filter(Rating.user_id.in_(fans), Rating.book_id != book_id, Rating.score >= 4)
        .group_by(Book.id)
        .order_by(func.count(Rating.id).desc())
        .limit(4)
        .all()
        if fans else []
    )
    return render_template(
        "book_detail.html", book=book, my_rating=my_rating,
        also=[a[0] for a in also],
    )


@main_bp.route("/book/<int:book_id>/rate", methods=["POST"])
@login_required
def rate(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    try:
        score = int(request.form.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    if score < 1 or score > 5:
        flash("Please choose a rating between 1 and 5 stars.", "error")
        return redirect(url_for("main.book_detail", book_id=book_id))

    review = (request.form.get("review") or "").strip()
    rating = Rating.query.filter_by(
        user_id=current_user.id, book_id=book_id
    ).first()
    if rating:
        rating.score = score
        rating.review = review
        flash("Your rating was updated.", "success")
    else:
        db.session.add(Rating(
            user_id=current_user.id, book_id=book_id,
            score=score, review=review,
        ))
        flash("Thanks for rating!", "success")
    db.session.commit()

    # Recompute recommendations on demand (per the spec).
    current_app.recommender.invalidate()
    return redirect(url_for("main.book_detail", book_id=book_id))


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name = (request.form.get("name") or current_user.name).strip()
        current_user.bio = (request.form.get("bio") or "")[:280]
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("main.profile"))

    my_ratings = (
        Rating.query.filter_by(user_id=current_user.id)
        .order_by(Rating.score.desc())
        .all()
    )
    avg_given = (
        round(sum(r.score for r in my_ratings) / len(my_ratings), 2)
        if my_ratings else 0
    )
    # Favourite genre
    genre_counts = {}
    for r in my_ratings:
        if r.score >= 4 and r.book.genre:
            genre_counts[r.book.genre] = genre_counts.get(r.book.genre, 0) + 1
    fav_genre = max(genre_counts, key=genre_counts.get) if genre_counts else "—"

    return render_template(
        "profile.html", my_ratings=my_ratings,
        avg_given=avg_given, fav_genre=fav_genre,
    )
