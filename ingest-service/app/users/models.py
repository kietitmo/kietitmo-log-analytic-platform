"""
Database models for the ingest service.
"""
import uuid
from sqlalchemy import Column, String, TIMESTAMP, Index, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

from app.common.db_types import StringList
from app.common.database import Base

class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
    )

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Store roles and permissions as arrays
    # Note: ARRAY is PostgreSQL-specific. For SQLite compatibility in tests,
    # consider using JSON or separate tables
    roles = Column(StringList, default=list, nullable=False)
    permissions = Column(StringList, default=list, nullable=False)
    
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login = Column(TIMESTAMP(timezone=True))

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username={self.username}, email={self.email})>"
