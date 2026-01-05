"""
Tests for database module.
"""
import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.common.database import get_db, check_db_connection, init_db
from app.jobs.models import Job
from app.common.constants import JobStatus, JobType


class TestDatabase:
    """Test cases for database module."""
    
    def test_get_db_context(self, db_session):
        """Test database context manager."""
        from app.common.database import get_db_context
        
        with get_db_context() as db:
            assert db is not None
            # Test that we can query
            jobs = db.query(Job).all()
            assert isinstance(jobs, list)
    
    def test_get_db_dependency(self, db_session):
        """Test get_db dependency."""
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        assert db == db_session
        
        # Cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_check_db_connection_success(self, db_engine):
        """Test successful database connection check."""
        # Patch the engine to use test engine
        from app import database
        original_engine = database.engine
        database.engine = db_engine
        
        try:
            result = check_db_connection()
            # Should return True if connection works
            assert result is True
        finally:
            database.engine = original_engine
    
    def test_init_db(self, db_engine):
        """Test database initialization."""
        # Tables should already be created by fixture
        # Just verify they exist
        from sqlalchemy import inspect
        
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        
        assert "jobs" in tables
        assert "file_uploads" in tables

