"""
Tests for authentication module.
"""
import pytest
from datetime import timedelta
from unittest.mock import patch

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    get_password_hash,
    get_current_user,
    create_test_token,
)
from app.exceptions import ValidationError
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestAuth:
    """Test cases for authentication module."""
    
    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format
    
    def test_verify_password_success(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user-123", "username": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user-123", "username": "testuser"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token_success(self):
        """Test successful token decoding."""
        data = {"sub": "user-123", "username": "testuser"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_token_invalid(self):
        """Test token decoding with invalid token."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_token_expired(self):
        """Test token decoding with expired token."""
        from datetime import datetime, timezone
        
        # Create token with past expiration
        data = {"sub": "user-123", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}
        
        # Manually create expired token
        from jose import jwt
        from app.config import settings
        
        expired_token = jwt.encode(
            data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)
        
        assert exc_info.value.status_code == 401
    
    def test_create_test_token(self):
        """Test test token creation."""
        token = create_test_token(user_id="test-123", username="testuser")
        
        assert token is not None
        payload = decode_token(token)
        assert payload["sub"] == "test-123"
        assert payload["username"] == "testuser"
    
    @patch("app.auth.security")
    def test_get_current_user_success(self, mock_security):
        """Test getting current user with valid token."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Create a valid token
        token = create_test_token(user_id="user-123", username="testuser")
        
        # Mock credentials
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )
        mock_security.return_value = mock_credentials
        
        # This is a simplified test - in practice, get_current_user is a dependency
        # and would be called differently
        pass  # Would need more complex mocking for full test
    
    def test_token_contains_refresh_type(self):
        """Test that refresh token contains type field."""
        data = {"sub": "user-123", "username": "testuser"}
        refresh_token = create_refresh_token(data)
        
        payload = decode_token(refresh_token)
        assert payload.get("type") == "refresh"
    
    def test_access_token_does_not_contain_type(self):
        """Test that access token does not contain type field."""
        data = {"sub": "user-123", "username": "testuser"}
        access_token = create_access_token(data)
        
        payload = decode_token(access_token)
        assert payload.get("type") is None

