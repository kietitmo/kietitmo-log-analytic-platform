# app/users/router.py
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.common.database import get_db
from app.users.service import UserService
from app.users.schemas.requests import (
    UserCreateRequest,
    UserProfileUpdateRequest,
    ChangePasswordRequest,
    UpdateUserRolesRequest,
)
from app.users.schemas.commands import (
    CreateUserCommand,
    UpdateUserProfileCommand,
    ChangeUserPasswordCommand,
    UpdateUserRolesCommand,
)

from app.users.schemas.requests import UpdateUserPermissionsRequest
from app.users.schemas.commands import UpdateUserPermissionsCommand, UpdateUserStatusCommand

from app.users.schemas.responses import UserResponse
from app.auth.models import Permission
from app.auth.dependencies import require_permissions, require_policy
from app.auth.authorization import OwnerOrPermissionPolicy

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions(Permission.USER_CREATE))],
)
def create_user(user_data: UserCreateRequest, db: Session = Depends(get_db)):
    command = CreateUserCommand(**user_data.model_dump())
    user = UserService.create_user(db, command)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[
        Depends(
            require_policy(
                OwnerOrPermissionPolicy(
                    permission=Permission.USER_VIEW_ANY,
                    resource_param="user_id",
                ),
                path_param="user_id",
            )
        )
    ],
)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = UserService.get_user_or_raise(db, user_id)
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=List[UserResponse],
    dependencies=[Depends(require_permissions(Permission.USER_LIST))],
)
def list_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    users = UserService.list_users(db, limit=limit, offset=offset)
    return [UserResponse.model_validate(u) for u in users]


@router.patch(
    "/{user_id}/profile",
    response_model=UserResponse,
)
def update_profile(
    user_id: str,
    data: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
):
    command = UpdateUserProfileCommand(user_id=user_id, email=data.email)
    user = UserService.update_profile(db, command)
    db.commit()
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password(
    user_id: str,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
):
    command = ChangeUserPasswordCommand(
        user_id=user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    UserService.change_password(db, command)
    db.commit()


@router.patch(
    "/{user_id}/roles",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(Permission.USER_UPDATE_ROLE))],
)
def update_roles(
    user_id: str,
    data: UpdateUserRolesRequest,
    db: Session = Depends(get_db),
):
    command = UpdateUserRolesCommand(user_id=user_id, roles=data.roles)
    user = UserService.update_roles(db, command)
    db.commit()
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/permissions",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(Permission.USER_UPDATE_PERMISSION))],
)
def update_permissions(
    user_id: str,
    data: UpdateUserPermissionsRequest,
    db: Session = Depends(get_db),
):
    command = UpdateUserPermissionsCommand(
        user_id=user_id,
        permissions=data.permissions,
    )
    user = UserService.update_permissions(db, command)
    db.commit()
    return UserResponse.model_validate(user)



@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions(Permission.USER_UPDATE_STATUS))],
)
def update_status(
    user_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
):
    command = UpdateUserStatusCommand(
        user_id=user_id,
        is_active=is_active,
    )
    user = UserService.update_status(db, command)
    db.commit()
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions(Permission.USER_DELETE))],
)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    UserService.delete_user(db, user_id)
    db.commit()
