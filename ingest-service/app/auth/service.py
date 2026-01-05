"""
Authentication service for login and user authentication.
"""
from sqlalchemy.orm import Session

from app.users.service import UserService
from app.auth.exceptions import InvalidCredentials, InactiveUser
from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.utils import verify_password


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def login(db: Session, username: str, password: str) -> dict:
        """
        Authenticate user and generate tokens.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            Dictionary with access_token, refresh_token, and user
            
        Raises:
            InvalidCredentials: If username/password is incorrect
            InactiveUser: If user is inactive
        """
        user = UserService.find_user_by_username(db, username)

        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentials()

        if not user.is_active:
            raise InactiveUser()

        UserService.update_last_login(db, user)

        token_payload = {
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles or [],
            "permissions": user.permissions or [],
        }

        return {
            "access_token": create_access_token(token_payload),
            "refresh_token": create_refresh_token(token_payload),
            "user": user,
        }

