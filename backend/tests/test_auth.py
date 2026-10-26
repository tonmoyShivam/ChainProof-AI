"""Authentication API tests."""

from __future__ import annotations

from tests.conftest import register_and_login


def test_register_login_me_logout(client) -> None:
    token = register_and_login(client)
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "dev@example.com"
    assert body["role"] == "user"

    logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200


def test_duplicate_email_rejected(client) -> None:
    register_and_login(client, email="dup@example.com")
    again = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123", "display_name": "X"},
    )
    assert again.status_code == 400


def test_login_rejects_bad_password(client) -> None:
    register_and_login(client, email="bad@example.com")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bad@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_route_requires_auth(client) -> None:
    response = client.get("/api/v1/models")
    assert response.status_code == 401
