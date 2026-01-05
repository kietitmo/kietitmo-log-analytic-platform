"""
Tests for auth router.
"""
import pytest
from unittest.mock import patch

from app.auth.jwt import create_access_token


class TestAuthRouter:
    """Test cases for auth router."""
    
    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
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
        """Test successful token refresh."""
        # First login to get tokens
        login_response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
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
        # First login to get tokens
        login_response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        access_token = login_response.json()["access_token"]
        
        # Try to refresh with access token
        response = client.post(
            "/auth/refresh",
            json={
                "refresh_token": access_token,
            },
        )
        
        assert response.status_code == 401
    
    def test_get_me_with_valid_token(self, client):
        """Test getting current user with valid token."""
        # Login first
        login_response = client.post(
            "/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        access_token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert data["username"] == "admin"
    
    def test_get_me_without_token(self, client):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        
        assert response.status_code == 403
    
    def test_get_me_with_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        
        assert response.status_code == 401
    
    def test_verify_token_valid(self, client):
        """Test verifying a valid token."""
        # Create a test token
        from app.auth.jwt import create_access_token
        token_data = {
            "sub": "test-123",
            "username": "testuser",
            "email": "testuser@test.com",
            "roles": ["user"],
            "permissions": [],
        }
        token = create_access_token(token_data)
        
        response = client.post(
            "/auth/verify",
            json={"token": token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "payload" in data
    
    def test_verify_token_invalid(self, client):
        """Test verifying an invalid token."""
        response = client.post(
            "/auth/verify",
            json={"token": "invalid.token"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "error" in data
    
    def test_login_rate_limit(self, client):
        """Test login rate limiting."""
        # Try to login multiple times quickly
        for i in range(6):  # Limit is 5 per minute
            response = client.post(
                "/auth/login",
                json={
                    "username": "admin",
                    "password": "wrongpassword",  # Wrong password to avoid success
                },
            )
        
        # Last request should be rate limited
        assert response.status_code == 429

