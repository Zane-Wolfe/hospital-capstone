import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.auth.service import (
    authenticate_user,
    create_tokens,
    verify_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_creates_hash(self):
        password = "test_password"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False


class TestAuthentication:
    def test_authenticate_user_valid(self):
        user = authenticate_user("admin", "secure_hospital_password")
        assert user is not None
        assert user.username == "admin"

    def test_authenticate_user_invalid_username(self):
        user = authenticate_user("invalid_user", "secure_hospital_password")
        assert user is None

    def test_authenticate_user_invalid_password(self):
        user = authenticate_user("admin", "wrong_password")
        assert user is None


class TestTokens:
    def test_create_tokens(self):
        tokens = create_tokens("testuser")
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    def test_verify_access_token(self):
        tokens = create_tokens("testuser")
        token_data = verify_token(tokens.access_token, token_type="access")
        assert token_data is not None
        assert token_data.username == "testuser"

    def test_verify_refresh_token(self):
        tokens = create_tokens("testuser")
        token_data = verify_token(tokens.refresh_token, token_type="refresh")
        assert token_data is not None
        assert token_data.username == "testuser"

    def test_verify_invalid_token(self):
        token_data = verify_token("invalid_token", token_type="access")
        assert token_data is None


class TestAuthEndpoints:
    def test_login_success(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "secure_hospital_password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong_password"},
        )
        assert response.status_code == 401

    def test_get_me_authenticated(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"

    def test_get_me_unauthenticated(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_refresh_token(self, client):
        # First login to get tokens
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "secure_hospital_password"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new tokens
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_logout(self, client, auth_headers):
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == 200
