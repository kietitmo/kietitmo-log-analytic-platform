"""
Authentication router for login and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    get_current_user,
)
import bcrypt


def verify_password_bcrypt(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly (bypassing passlib)."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False
from app.middleware.rate_limit import rate_limit
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Unauthorized"},
        429: {"description": "Rate limit exceeded"},
    },
)

security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


# In-memory user store for demo purposes
# In production, this should be in a database
# Store plain passwords, will be hashed using bcrypt directly (bypassing passlib issues)
_DEMO_USERS_DATA = {
    "admin": {
        "user_id": "admin-001",
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "admin"],
    },
    "user": {
        "user_id": "user-001",
        "username": "user",
        "email": "user@example.com",
        "password": "user123",
        "roles": ["user"],
        "permissions": ["read", "write"],
    },
}

# Cache for hashed passwords
_DEMO_USERS_CACHE = {}


def _hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt directly (bypassing passlib)."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _get_demo_user(username: str) -> Optional[dict]:
    """Get demo user, hashing password on first access using bcrypt directly."""
    if username not in _DEMO_USERS_DATA:
        return None
    
    if username not in _DEMO_USERS_CACHE:
        user_data = _DEMO_USERS_DATA[username].copy()
        # Use bcrypt directly to avoid passlib issues
        user_data["hashed_password"] = _hash_password_bcrypt(user_data["password"])
        del user_data["password"]
        _DEMO_USERS_CACHE[username] = user_data
    
    return _DEMO_USERS_CACHE[username]


class DemoUsers:
    """Dict-like accessor for demo users."""
    
    def get(self, key: str, default=None):
        """Get user by username."""
        user = _get_demo_user(key)
        return user if user else default
    
    def __getitem__(self, key: str):
        """Get user by username."""
        user = _get_demo_user(key)
        if not user:
            raise KeyError(key)
        return user
    
    def __contains__(self, key: str) -> bool:
        """Check if user exists."""
        return key in _DEMO_USERS_DATA


DEMO_USERS = DemoUsers()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Authenticate user and get access/refresh tokens",
)
@rate_limit(requests=5, period="minute")  # Limit login attempts
def login(request: Request, credentials: LoginRequest) -> TokenResponse:
    """
    Login endpoint.
    
    Authenticates a user and returns JWT access and refresh tokens.
    
    Args:
        credentials: Login credentials
        
    Returns:
        TokenResponse with access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = DEMO_USERS.get(credentials.username)
    
    # Use bcrypt directly for demo users to avoid passlib issues
    if not user or not verify_password_bcrypt(credentials.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    token_data = {
        "sub": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "roles": user["roles"],
        "permissions": user["permissions"],
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info(f"User logged in: {user['username']} ({user['user_id']})")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh token",
    description="Get new access token using refresh token",
)
@rate_limit(requests=10, period="minute")
def refresh_token(http_request: Request, request: RefreshTokenRequest) -> TokenResponse:
    """
    Refresh access token.
    
    Uses a refresh token to get a new access token.
    
    Args:
        request: Refresh token request
        
    Returns:
        TokenResponse with new access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = decode_token(request.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # Get user info from token
        user_id = payload.get("sub")
        username = payload.get("username")
        
        # In production, fetch user from database
        # For demo, we'll create new tokens with the same data
        token_data = {
            "sub": user_id,
            "username": username,
            "email": payload.get("email"),
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"Token refreshed for user: {username} ({user_id})")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user",
)
def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current user information.
    
    Returns information about the authenticated user.
    
    Args:
        current_user: Current authenticated user (from dependency)
        
    Returns:
        User information
    """
    return current_user


@router.post(
    "/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify token",
    description="Verify if a token is valid",
)
def verify_token(token: str) -> dict:
    """
    Verify a token.
    
    Checks if a token is valid and returns its payload.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Token payload if valid
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = decode_token(token)
        return {
            "valid": True,
            "payload": payload,
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": str(e.detail),
        }

