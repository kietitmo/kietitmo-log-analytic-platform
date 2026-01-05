from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.authorization import resolve_auth_context, resolve_permissions, Policy, OwnerOrPermissionPolicy
from app.auth.exceptions import InvalidToken, PermissionDenied, PolicyDenied
from app.auth.jwt import decode_token
from app.auth.models import Permission
from app.auth.schemas import AuthUser
from app.common.config import settings

security = HTTPBearer(auto_error=False)

def require_permissions(*required: Permission):
    def dependency(current_user = Depends(get_current_user)):
        user_permissions = resolve_permissions(current_user)

        if not user_permissions.intersection(required):
            raise PermissionDenied()

        return current_user

    return dependency


def require_policy(policy: Policy, path_param: str):
    def dependency(
        request: Request,
        current_user: dict = Depends(get_current_user),
    ):
        ctx = resolve_auth_context(current_user)

        resource_id = request.path_params.get(path_param)

        if not policy.check(ctx, **{path_param: resource_id}):
            raise PolicyDenied()

        return ctx

    return dependency

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> AuthUser:
        
        if credentials is None:
            raise InvalidToken()
        
        token = credentials.credentials

        if token.startswith(settings.JWT_TOKEN_PREFIX + " "):
            token = token[len(settings.JWT_TOKEN_PREFIX) + 1:]

        payload = decode_token(token)

        return AuthUser(
            user_id=payload["sub"],
            username=payload["username"],
            email=payload["email"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
        )