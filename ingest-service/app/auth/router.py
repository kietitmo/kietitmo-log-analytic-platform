# app/auth/router.py
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.auth.schemas import LoginRequest, TokenResponse, RefreshTokenRequest, AuthUser
from app.auth.service import AuthService
from app.auth.jwt import decode_token, create_access_token, create_refresh_token
from app.auth.dependencies import get_current_user
from app.common.middleware.rate_limit import rate_limit
from app.common.config import settings
from app.auth.exceptions import InvalidToken

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
@rate_limit(requests=5, period="minute")
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    result = AuthService.login(
        db=db,
        username=credentials.username,
        password=credentials.password,
    )
    db.commit()

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    from app.users.user_service import UserService
    
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise InvalidToken()
    
    # Validate user still exists and is active
    user = UserService.find_user_by_id(db, payload.get("sub"))
    if not user or not user.is_active:
        raise InvalidToken()

    token_data = {
        "sub": user.user_id,
        "username": user.username,
        "email": user.email,
        "roles": user.roles or [],
        "permissions": user.permissions or [],
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
def me(
    current_user: AuthUser = Depends(get_current_user),
):
    return current_user
