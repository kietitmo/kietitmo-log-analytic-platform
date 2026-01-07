"""
Tests for auth router.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.auth.dependencies import get_current_user
from app.main import app

class TestAuthRouter:
    """Test cases for auth router."""
    
    def test_login_success(self, client):
        fake_user = MagicMock()
        fake_user.user_id = "u-001"
        fake_user.username = "admin"
        fake_user.email = "admin@test.com"
        fake_user.roles = ["admin"]
        fake_user.permissions = []
        fake_user.is_active = True
        fake_user.hashed_password = "hashed"

        with patch(
            "app.auth.service.UserService.find_user_by_username",
            return_value=fake_user,
        ), patch(
            "app.auth.service.verify_password",
            return_value=True,
        ):
            response = client.post(
                "/auth/login",
                json={"username": "admin", "password": "admin123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "password",
            },
        )
        
        assert response.status_code == 401
    
    def test_refresh_token_success(self, client):
        fake_payload = {
            "sub": "u-001",
            "username": "admin",
            "email": "admin@test.com",
            "roles": ["admin"],
            "permissions": [],
        }

        with patch(
            "app.auth.router.AuthService.refresh_token",
            return_value=fake_payload,
        ):
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "valid.refresh.token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    
    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid.token.here",
            },
        )
        
        assert response.status_code == 401
    
    def test_refresh_token_with_access_token(self, client):
        """Test token refresh with access token (should fail)."""
        # Try to refresh with access token
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "access_token",
            },
        )
        
        assert response.status_code == 401
    

    def test_get_me_with_valid_token(self, client):
        fake_user = {
            "user_id": "u-001",
            "username": "admin",
            "email": "admin@test.com",
            "roles": ["admin"],
            "permissions": [],
        }

        app.dependency_overrides[get_current_user] = lambda: fake_user

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer faketoken"},
        )

        assert response.status_code == 200
        assert response.json()["username"] == "admin"

        app.dependency_overrides.clear()

    
    def test_get_me_without_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    
    def test_get_me_with_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        
        assert response.status_code == 401
    
