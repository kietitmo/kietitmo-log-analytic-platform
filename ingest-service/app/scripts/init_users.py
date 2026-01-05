"""
Script to initialize default users in the database.
Run this script once to create initial admin and user accounts.
"""
from app.common.database import SessionLocal, init_db
from app.users.service import UserService
from app.auth.models import Role, Permission
from app.common.logger import setup_logging, get_logger
from app.users.schemas.commands import CreateUserCommand

setup_logging()
logger = get_logger(__name__)


def init_default_users():
    """Initialize default users in the database."""
    db = SessionLocal()
    
    try:
        # Initialize database tables
        init_db()
        logger.info("Database tables initialized")
        
        # Check if admin user exists
        admin_user = UserService.find_user_by_username(db, "admin")
        if not admin_user:
            # Create admin user
            command = CreateUserCommand(
                username="admin",
                email="admin@example.com",
                password="admin123",
                roles=[Role.ADMIN, Role.USER],
                permissions=[],  # ❌ không set tay
                is_active=True,
                is_superuser=True,
            )

            admin_user = UserService.create_user(db, command)
            logger.info("Created admin user: admin / admin123")
        else:
            logger.info("Admin user already exists")
        
        # Check if regular user exists
        regular_user = UserService.find_user_by_username(db, "user")
        if not regular_user:
            # Create regular user
            command = CreateUserCommand(
                username="user",
                email="user@example.com",
                password="user123",
                roles=[Role.USER],
                permissions=[Permission.USER_VIEW, Permission.USER_UPDATE],
                is_active=True,
                is_superuser=False,
            )

            regular_user = UserService.create_user(
                db=db,
                command=command,
            )
            logger.info("Created regular user: user / user123")
        else:
            logger.info("Regular user already exists")
        
        db.commit()
        logger.info("Default users initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize users: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing default users...")
    init_default_users()
    print("Done!")

