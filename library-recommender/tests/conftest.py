"""Shared PyTest fixtures."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models import User, Book, Rating


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded(app):
    """A small, deterministic dataset with clear taste clusters."""
    with app.app_context():
        # Books
        b = {}
        specs = [
            ("Fantasy A", "Fantasy"), ("Fantasy B", "Fantasy"),
            ("SciFi A", "Sci-Fi"), ("SciFi B", "Sci-Fi"),
            ("Mystery A", "Mystery"), ("Mystery B", "Mystery"),
        ]
        for title, genre in specs:
            book = Book(title=title, author="Author", genre=genre, isbn=title)
            db.session.add(book)
            db.session.flush()
            b[title] = book.id

        # Users
        def mk(name):
            u = User(name=name, email=f"{name}@t.dev")
            u.set_password("password123")
            db.session.add(u)
            db.session.flush()
            return u.id

        alice = mk("alice")   # loves fantasy
        bob = mk("bob")       # loves fantasy (similar to alice)
        carol = mk("carol")   # loves mystery
        target = mk("target") # loves fantasy, hasn't read Fantasy B

        def rate(uid, title, score):
            db.session.add(Rating(user_id=uid, book_id=b[title], score=score))

        # alice & bob: high fantasy, low mystery  -> similar
        for uid in (alice, bob):
            rate(uid, "Fantasy A", 5); rate(uid, "Fantasy B", 5)
            rate(uid, "SciFi A", 3);   rate(uid, "Mystery A", 1)
        # carol: opposite taste
        rate(carol, "Fantasy A", 1); rate(carol, "Mystery A", 5)
        rate(carol, "Mystery B", 5); rate(carol, "SciFi A", 2)
        # target: likes fantasy A, hasn't rated Fantasy B (the expected rec)
        rate(target, "Fantasy A", 5); rate(target, "SciFi A", 3)
        rate(target, "Mystery A", 1)

        db.session.commit()
        return {"books": b, "alice": alice, "bob": bob, "carol": carol, "target": target}


@pytest.fixture
def auth_client(client, app):
    """A client logged in as a freshly-registered user."""
    client.post("/register", data={
        "name": "Tester", "email": "tester@t.dev", "password": "password123",
    }, follow_redirects=True)
    return client
