from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import settings

NEW_USER = {"email": "alex@test.com", "display_name": "alex", "password": "secret123"}


def register(client, **changes):
    return client.post("/api/auth/register", json={**NEW_USER, **changes})


def login(client, email="alex@test.com", password="secret123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def use_token(client, token):
    """Throw away the real cookie and send this token instead."""
    client.cookies.clear()
    client.cookies.set("access_token", token)


def make_token(user_id, key=settings.jwt_secret, expires_in=timedelta(days=1)):
    payload = {"sub": str(user_id), "exp": datetime.now(UTC) + expires_in}
    return jwt.encode(payload, key, algorithm="HS256")


# ---------- register ----------

def test_register_returns_new_user(client):
    r = register(client)
    assert r.status_code == 201
    user = r.json()
    assert user["email"] == "alex@test.com"
    assert user["display_name"] == "alex"
    assert user["elo"] == 1200
    assert "password" not in user
    assert "password_hash" not in user


def test_register_logs_you_in(client):
    register(client)
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["display_name"] == "alex"


def test_login_cookie_is_protected(client):
    cookie = register(client).headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie


def test_email_is_saved_lowercase(client):
    assert register(client, email="Alex@Test.COM").json()["email"] == "alex@test.com"


def test_email_already_taken(client):
    register(client)
    r = register(client, email="ALEX@test.com", display_name="other")
    assert r.status_code == 409
    assert r.json()["detail"] == "Email is already taken"


def test_display_name_already_taken(client):
    register(client)
    r = register(client, email="other@test.com")
    assert r.status_code == 409
    assert r.json()["detail"] == "Display name is already taken"


@pytest.mark.parametrize(
    "changes",
    [
        {"password": "short1"},  # under 8 characters
        {"password": "onlyletters"},  # no digit
        {"password": "12345678"},  # no letter
        {"display_name": "ab"},  # under 3 characters
        {"display_name": "a b"},  # space not allowed
        {"email": "not-an-email"},
        {"is_admin": True},  # unknown field
    ],
)
def test_register_rejects_bad_input(client, changes):
    assert register(client, **changes).status_code == 422


# ---------- login / logout ----------

def test_login(client):
    register(client)
    client.cookies.clear()
    r = login(client, email="ALEX@test.com")
    assert r.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


@pytest.mark.parametrize(
    "email, password",
    [
        ("alex@test.com", "wrong1234"),  # wrong password
        ("nobody@test.com", "secret123"),  # no such user
    ],
)
def test_login_fails(client, email, password):
    register(client)
    client.cookies.clear()
    r = login(client, email, password)
    assert r.status_code == 401
    assert r.json()["detail"] == "Wrong email or password"
    assert client.get("/api/auth/me").status_code == 401


def test_logout(client):
    register(client)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


# ---------- who is logged in ----------

def test_me_without_login(client):
    assert client.get("/api/auth/me").status_code == 401


def test_garbage_token(client):
    use_token(client, "garbage")
    assert client.get("/api/auth/me").status_code == 401


def test_token_signed_with_wrong_key(client):
    user_id = register(client).json()["id"]
    use_token(client, make_token(user_id, key="x" * 64))
    assert client.get("/api/auth/me").status_code == 401


def test_expired_token(client):
    user_id = register(client).json()["id"]
    use_token(client, make_token(user_id, expires_in=timedelta(seconds=-1)))
    assert client.get("/api/auth/me").status_code == 401


def test_token_for_deleted_user(client):
    use_token(client, make_token(999))
    assert client.get("/api/auth/me").status_code == 401


def test_other_pages_need_login(client):
    assert client.get("/api/friends").status_code == 401