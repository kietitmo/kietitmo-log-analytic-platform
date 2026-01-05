# app/users/schemas/commands.py
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from app.auth.models import Role, Permission


class CreateUserCommand(BaseModel):
    username: str
    email: EmailStr
    password: str
    roles: List[Role]
    permissions: List[Permission]
    is_active: bool
    is_superuser: bool

class UserUpdateCommand(BaseModel):
    user_id: str
    email: Optional[EmailStr] = None
    roles: Optional[List[Role]] = None
    permissions: Optional[List[Permission]] = None
    is_active: Optional[bool] = None

class UpdateUserProfileCommand(BaseModel):
    user_id: str
    email: Optional[EmailStr]


class ChangeUserPasswordCommand(BaseModel):
    user_id: str
    current_password: str
    new_password: str


class UpdateUserRolesCommand(BaseModel):
    user_id: str
    roles: List[Role]


class UpdateUserPermissionsCommand(BaseModel):
    user_id: str
    permissions: List[Permission]


class ActivateUserCommand(BaseModel):
    user_id: str


class DeactivateUserCommand(BaseModel):
    user_id: str


class UpdateUserStatusCommand(BaseModel):
    user_id: str
    is_active: bool
