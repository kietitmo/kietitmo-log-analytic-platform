"""
Database configuration and session management.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.common.config import settings
from app.common.logger import get_logger
from app.common.exceptions.infrastucture import DatabaseError

logger = get_logger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas if using SQLite (for development)."""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    Ensures proper cleanup and error handling.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise DatabaseError(f"Database operation failed: {str(e)}") from e
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in database session: {e}", exc_info=True)
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use this for non-FastAPI dependency injection scenarios.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise DatabaseError(f"Database operation failed: {str(e)}") from e
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in database session: {e}", exc_info=True)
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        with engine.connect() as conn:
            # SQLAlchemy 2.0 requires text() wrapper for raw SQL
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

