"""Integration tests for registration, login, and access control."""
from app.extensions import db
from app.models import User


def test_register_creates_user_and_logs_in(client, app):
    resp = client.post("/register", data={
        "name": "Alice", "email": "alice@example.com", "password": "secret123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="alice@example.com").first() is not None


def test_register_rejects_short_password(client):
    resp = client.post("/register", data={
        "name": "Bob", "email": "bob@example.com", "password": "123",
    })
    assert b"at least 6 characters" in resp.data.lower()


def test_register_rejects_duplicate_email(client, app):
    data = {"name": "Bob", "email": "bob@example.com", "password": "secret123"}
    client.post("/register", data=data, follow_redirects=True)
    client.get("/logout", follow_redirects=True)
    resp = client.post("/register", data=data)
    assert b"already exists" in resp.data.lower()


def test_login_with_wrong_password_fails(client, app):
    with app.app_context():
        u = User(name="Carol", email="carol@example.com")
        u.set_password("rightpass")
        db.session.add(u)
        db.session.commit()
    resp = client.post("/login", data={"email": "carol@example.com", "password": "wrong"})
    assert b"invalid email or password" in resp.data.lower()


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_password_is_hashed_not_plaintext(app):
    with app.app_context():
        u = User(name="Dave", email="dave@example.com")
        u.set_password("plaintext123")
        assert u.password_hash != "plaintext123"
        assert u.check_password("plaintext123")
        assert not u.check_password("wrong")
