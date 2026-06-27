"""Integration tests for catalog, rating, profile, and admin guards."""
from app.extensions import db
from app.models import User, Book, Rating


def _login(client, email, password="password123"):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=True)


def test_catalog_lists_books(auth_client, app):
    with app.app_context():
        db.session.add(Book(title="Findable Book", author="X", genre="Sci-Fi", isbn="z1"))
        db.session.commit()
    resp = auth_client.get("/books")
    assert b"Findable Book" in resp.data


def test_search_filters_books(auth_client, app):
    with app.app_context():
        db.session.add(Book(title="Dune", author="Herbert", genre="Sci-Fi", isbn="z2"))
        db.session.add(Book(title="Hamlet", author="Shakespeare", genre="Classic", isbn="z3"))
        db.session.commit()
    resp = auth_client.get("/books?q=dune")
    assert b"Dune" in resp.data
    assert b"Hamlet" not in resp.data


def test_rating_a_book_persists(auth_client, app):
    with app.app_context():
        book = Book(title="Ratable", author="Y", genre="Mystery", isbn="z4")
        db.session.add(book)
        db.session.commit()
        book_id = book.id
    auth_client.post(f"/book/{book_id}/rate",
                     data={"score": "4", "review": "Great read"},
                     follow_redirects=True)
    with app.app_context():
        r = Rating.query.filter_by(book_id=book_id).first()
        assert r is not None and r.score == 4 and r.review == "Great read"


def test_re_rating_updates_not_duplicates(auth_client, app):
    with app.app_context():
        book = Book(title="Updatable", author="Y", genre="Mystery", isbn="z5")
        db.session.add(book)
        db.session.commit()
        book_id = book.id
    auth_client.post(f"/book/{book_id}/rate", data={"score": "2"}, follow_redirects=True)
    auth_client.post(f"/book/{book_id}/rate", data={"score": "5"}, follow_redirects=True)
    with app.app_context():
        ratings = Rating.query.filter_by(book_id=book_id).all()
        assert len(ratings) == 1 and ratings[0].score == 5


def test_invalid_score_rejected(auth_client, app):
    with app.app_context():
        book = Book(title="Boundary", author="Y", genre="Mystery", isbn="z6")
        db.session.add(book)
        db.session.commit()
        book_id = book.id
    auth_client.post(f"/book/{book_id}/rate", data={"score": "9"}, follow_redirects=True)
    with app.app_context():
        assert Rating.query.filter_by(book_id=book_id).count() == 0


def test_non_admin_blocked_from_admin(auth_client):
    resp = auth_client.get("/admin/")
    assert resp.status_code == 403


def test_admin_can_view_dashboard(client, app):
    with app.app_context():
        a = User(name="Admin", email="a@admin.dev", is_admin=True)
        a.set_password("password123")
        db.session.add(a)
        db.session.commit()
    _login(client, "a@admin.dev")
    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert b"Library overview" in resp.data


def test_admin_can_add_book(client, app):
    with app.app_context():
        a = User(name="Admin", email="a@admin.dev", is_admin=True)
        a.set_password("password123")
        db.session.add(a)
        db.session.commit()
    _login(client, "a@admin.dev")
    client.post("/admin/books/new", data={
        "title": "Brand New", "author": "Author", "genre": "Sci-Fi", "year": "2020",
    }, follow_redirects=True)
    with app.app_context():
        assert Book.query.filter_by(title="Brand New").first() is not None
