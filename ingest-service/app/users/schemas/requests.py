from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.auth.models import Role, Permission
from app.users.schemas.commands import CreateUserCommand, UserUpdateCommand

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    roles: list[Role] = []
    permissions: list[Permission] = []
    is_active: bool = True
    is_superuser: bool = False

    def to_command(self) -> CreateUserCommand:
        return CreateUserCommand(
            username=self.username,
            email=self.email,
            password=self.password,
            roles=self.roles,
            permissions=self.permissions,
            is_active=self.is_active,
            is_superuser=self.is_superuser,
        )

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    roles: Optional[List[Role]] = None
    permissions: Optional[List[Permission]] = None
    is_active: Optional[bool] = None

    def to_command(self, user_id: str) -> UserUpdateCommand:
        from app.users.schemas.commands import UserUpdateCommand  # Import here to avoid circular import
        return UserUpdateCommand(
            user_id=user_id,
            email=self.email,
            roles=self.roles,
            permissions=self.permissions,
            is_active=self.is_active,
        )

class UserProfileUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdateUserRolesRequest(BaseModel):
    roles: List[Role]


class UpdateUserPermissionsRequest(BaseModel):
    permissions: List[Permission]
