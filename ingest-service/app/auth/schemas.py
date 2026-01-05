from typing import List
from pydantic import BaseModel, Field
from app.auth.models import Role, Permission



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


class AuthUser(BaseModel):
    """
    Authenticated user identity extracted from JWT.
    Used for authorization & policies only.
    """
    user_id: str = Field(..., description="User unique identifier")
    username: str
    email: str

    roles: List[Role] = Field(default_factory=list)
    permissions: List[Permission] = Field(default_factory=list)

    model_config = {"frozen": True}
