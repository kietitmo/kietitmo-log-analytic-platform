"""
Authorization logic: permission resolution and policies.
"""
from app.auth.models import AuthContext, ROLE_PERMISSIONS, Permission, Role
from app.auth.schemas import AuthUser


def resolve_auth_context(current_user: AuthUser) -> AuthContext:
    """
    Resolve authentication context from user data.
    
    Combines explicit permissions with role-based permissions.
    """
    permissions: set[Permission] = set(
        Permission(p) for p in current_user.permissions or []
    )

    for role_str in current_user.roles or []:
        try:
            role = Role(role_str)
            permissions |= ROLE_PERMISSIONS.get(role, set())
        except ValueError:
            # Invalid role, skip
            continue

    return AuthContext(
        user_id=current_user.user_id,
        roles=set(current_user.roles or []),
        permissions=permissions,
    )


def resolve_permissions(user: AuthUser) -> set[Permission]:
    """
    Resolve all permissions for a user.
    
    Returns set of permissions from both explicit permissions and roles.
    """
    permissions = set(
        Permission(p) for p in (user.permissions or [])
    )

    for role_str in user.roles or []:
        try:
            role = Role(role_str)
            permissions |= ROLE_PERMISSIONS.get(role, set())
        except ValueError:
            # Invalid role, skip
            continue

    return permissions


class Policy:
    """Base policy class for authorization checks."""
    
    def check(self, ctx: AuthContext, **kwargs) -> bool:
        """Check if policy allows access."""
        raise NotImplementedError


class OwnerOrPermissionPolicy(Policy):
    """Policy that allows access if user owns resource or has permission."""
    
    def __init__(self, permission: Permission, resource_param: str):
        self.permission = permission
        self.resource_param = resource_param

    def check(self, ctx: AuthContext, **kwargs) -> bool:
        """Check if user owns resource or has required permission."""
        resource_owner_id = kwargs.get(self.resource_param)
        if ctx.user_id == resource_owner_id:
            return True

        return self.permission in ctx.permissions

