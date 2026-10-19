"""Tests for the auth module - register and login."""

from fastapi.testclient import TestClient


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "secret123", "full_name": "Alice"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "hashed_password" not in body  # must never leak the password hash in API responses


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "secret123", "full_name": "Bob"},
    )

    response = client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "anotherpassword", "full_name": "Bob Again"},
    )

    assert response.status_code == 409


def test_login_with_correct_credentials_returns_token(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "secret123", "full_name": "Carol"},
    )

    response = client.post("/auth/login", json={"email": "carol@example.com", "password": "secret123"})

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_is_rejected(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "secret123", "full_name": "Dave"},
    )

    response = client.post("/auth/login", json={"email": "dave@example.com", "password": "wrongpassword"})

    assert response.status_code == 401


def test_protected_route_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/users/me")

    assert response.status_code in (401, 403)  # FastAPI's HTTPBearer returns 403 for a missing header
