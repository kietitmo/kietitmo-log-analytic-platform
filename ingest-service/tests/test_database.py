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
        db_gen = get_db()
        db = next(db_gen)

        assert db is not None
        assert db.bind == db_session.bind

        try:
            next(db_gen)
        except StopIteration:
            pass

    
    def test_check_db_connection_success(self):
        result = check_db_connection()
        assert result is True

    
    def test_init_db(self, db_engine):
        from sqlalchemy import inspect

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        assert "jobs" in tables
        assert "file_uploads" in tables


