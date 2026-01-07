"""
Tests for exceptions module.
"""
import pytest
from fastapi import HTTPException

from app.common.exceptions.infrastucture import (
    InfrastructureException,
    StorageError,
    DatabaseError,
    QueueError,
)
from app.ingest.exceptions import IngestDomainException
from app.jobs.exceptions import (
    JobNotFoundError,
    InvalidJobStateError,
    JobDomainException
)



class TestExceptions:
    """Test cases for exceptions module."""
    
    def test_ingest_service_exception(self):
        """Test base exception."""
        exc = IngestDomainException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)
    
    def test_job_not_found_error(self):
        """Test JobNotFoundError."""
        exc = JobNotFoundError("Job not found")
        assert str(exc) == "Job not found"
        assert isinstance(exc, JobDomainException)
    
    def test_invalid_job_state_error(self):
        """Test InvalidJobStateError."""
        exc = InvalidJobStateError("Invalid state")
        assert str(exc) == "Invalid state"
        assert isinstance(exc, JobDomainException)
    
    def test_storage_error(self):
        """Test StorageError."""
        exc = StorageError("Storage error")
        assert str(exc) == "Storage error"
        assert isinstance(exc, InfrastructureException)
    
    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError("Database error")
        assert str(exc) == "Database error"
        assert isinstance(exc, InfrastructureException)
    
    def test_queue_error(self):
        """Test QueueError."""
        exc = QueueError("Queue error")
        assert str(exc) == "Queue error"
        assert isinstance(exc, InfrastructureException)
    
