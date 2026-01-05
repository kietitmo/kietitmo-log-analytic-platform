# app/services/user_service.py
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.users.models import User
from app.auth.utils import verify_password, get_password_hash
from app.common.logger import get_logger
from app.users.schemas.commands import (
    CreateUserCommand,
    UpdateUserProfileCommand,
    ChangeUserPasswordCommand,
    UpdateUserRolesCommand,
    UpdateUserPermissionsCommand,
    UpdateUserStatusCommand,
)
from app.users.exceptions import (
    UserNotFoundError,
    InvalidUserDataError,
)

logger = get_logger(__name__)


class UserService:

    # ---------- Queries (NO exception) ----------

    @staticmethod
    def find_user_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.user_id == user_id).first()

    @staticmethod
    def find_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def find_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def list_users(db: Session, offset: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(offset).limit(limit).all()

    # ---------- Guards ----------

    @staticmethod
    def get_user_or_raise(db: Session, user_id: str) -> User:
        user = UserService.find_user_by_id(db, user_id)
        if not user:
            raise UserNotFoundError()
        return user

    # ---------- Commands ----------

    @staticmethod
    def create_user(db: Session, command: CreateUserCommand) -> User:
        if UserService.find_user_by_username(db, command.username):
            raise InvalidUserDataError()

        if UserService.find_user_by_email(db, command.email):
            raise InvalidUserDataError()

        user = User(
            username=command.username,
            email=command.email,
            hashed_password=get_password_hash(command.password),
            roles=command.roles,
            permissions=command.permissions,
            is_active=command.is_active,
            is_superuser=command.is_superuser,
        )

        db.add(user)
        db.flush()

        logger.info("User created", extra={"user_id": user.user_id})
        return user

    @staticmethod
    def update_profile(db: Session, command: UpdateUserProfileCommand) -> User:
        user = UserService.get_user_or_raise(db, command.user_id)

        if command.email:
            user.email = command.email

        db.flush()
        return user

    @staticmethod
    def change_password(db: Session, command: ChangeUserPasswordCommand) -> None:
        user = UserService.get_user_or_raise(db, command.user_id)

        if not verify_password(command.current_password, user.hashed_password):
            raise InvalidUserDataError()

        user.hashed_password = get_password_hash(command.new_password)
        db.flush()

    @staticmethod
    def update_roles(db: Session, command: UpdateUserRolesCommand) -> User:
        user = UserService.get_user_or_raise(db, command.user_id)
        user.roles = command.roles
        db.flush()
        return user

    @staticmethod
    def update_permissions(db: Session, command: UpdateUserPermissionsCommand) -> User:
        user = UserService.get_user_or_raise(db, command.user_id)
        user.permissions = command.permissions
        db.flush()
        return user

    @staticmethod
    def update_status(db: Session, command: UpdateUserStatusCommand) -> User:
        user = UserService.get_user_or_raise(db, command.user_id)
        user.is_active = command.is_active
        db.flush()
        return user

    @staticmethod
    def update_last_login(db: Session, user: User) -> None:
        user.last_login = datetime.utcnow()
        db.flush()

    @staticmethod
    def delete_user(db: Session, user_id: str) -> None:
        user = UserService.get_user_or_raise(db, user_id)
        db.delete(user)
        db.flush()
