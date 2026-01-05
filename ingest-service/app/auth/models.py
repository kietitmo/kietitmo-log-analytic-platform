"""
Auth domain models: roles, permissions, and context.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Set


class Role(str, Enum):
    """User roles."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class Permission(str, Enum):
    """User permissions."""
    USER_CREATE = "user:create"
    USER_VIEW = "user:view"
    USER_VIEW_ANY = "user:view:any"
    USER_LIST = "user:list"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Fine-grained user update permissions
    USER_UPDATE_PROFILE = "user:update:profile"
    USER_UPDATE_PASSWORD = "user:update:password"
    USER_UPDATE_ROLE = "user:update:role"
    USER_UPDATE_PERMISSION = "user:update:permission"
    USER_UPDATE_STATUS = "user:update:status"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.USER_CREATE,
        Permission.USER_VIEW_ANY,
        Permission.USER_LIST,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
    },
    Role.MANAGER: {
        Permission.USER_VIEW_ANY,
        Permission.USER_LIST,
        Permission.USER_UPDATE_PROFILE,
        Permission.USER_UPDATE_STATUS,
    },
    Role.USER: {
        Permission.USER_VIEW,
        Permission.USER_UPDATE_PROFILE,
        Permission.USER_UPDATE_PASSWORD,
    },
}


@dataclass(frozen=True)
class AuthContext:
    """Authentication context for authorization checks."""
    user_id: str
    roles: set[str]
    permissions: Set[Permission]

