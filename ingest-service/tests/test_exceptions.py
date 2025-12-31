"""
Tests for exceptions module.
"""
import pytest
from fastapi import HTTPException

from app.exceptions import (
    IngestServiceException,
    JobNotFoundError,
    InvalidJobStateError,
    StorageError,
    DatabaseError,
    QueueError,
    ValidationError,
    handle_service_exception,
)


class TestExceptions:
    """Test cases for exceptions module."""
    
    def test_ingest_service_exception(self):
        """Test base exception."""
        exc = IngestServiceException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)
    
    def test_job_not_found_error(self):
        """Test JobNotFoundError."""
        exc = JobNotFoundError("Job not found")
        assert str(exc) == "Job not found"
        assert isinstance(exc, IngestServiceException)
    
    def test_invalid_job_state_error(self):
        """Test InvalidJobStateError."""
        exc = InvalidJobStateError("Invalid state")
        assert str(exc) == "Invalid state"
        assert isinstance(exc, IngestServiceException)
    
    def test_storage_error(self):
        """Test StorageError."""
        exc = StorageError("Storage error")
        assert str(exc) == "Storage error"
        assert isinstance(exc, IngestServiceException)
    
    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError("Database error")
        assert str(exc) == "Database error"
        assert isinstance(exc, IngestServiceException)
    
    def test_queue_error(self):
        """Test QueueError."""
        exc = QueueError("Queue error")
        assert str(exc) == "Queue error"
        assert isinstance(exc, IngestServiceException)
    
    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Validation error")
        assert str(exc) == "Validation error"
        assert isinstance(exc, IngestServiceException)
    
    def test_handle_service_exception_job_not_found(self):
        """Test handling JobNotFoundError."""
        exc = JobNotFoundError("Job not found")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 404
        assert "not found" in http_exc.detail.lower()
    
    def test_handle_service_exception_invalid_state(self):
        """Test handling InvalidJobStateError."""
        exc = InvalidJobStateError("Invalid state")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert "state" in http_exc.detail.lower()
    
    def test_handle_service_exception_storage_error(self):
        """Test handling StorageError."""
        exc = StorageError("Storage unavailable")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 503
        assert "storage" in http_exc.detail.lower()
    
    def test_handle_service_exception_database_error(self):
        """Test handling DatabaseError."""
        exc = DatabaseError("Database error")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 503
        assert "database" in http_exc.detail.lower()
    
    def test_handle_service_exception_queue_error(self):
        """Test handling QueueError."""
        exc = QueueError("Queue error")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 503
        assert "queue" in http_exc.detail.lower()
    
    def test_handle_service_exception_validation_error(self):
        """Test handling ValidationError."""
        exc = ValidationError("Validation error")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 422
        assert "validation" in http_exc.detail.lower()
    
    def test_handle_service_exception_unknown(self):
        """Test handling unknown exception."""
        exc = IngestServiceException("Unknown error")
        http_exc = handle_service_exception(exc)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 500
        assert "error" in http_exc.detail.lower()
    
    def test_handle_service_exception_custom_message(self):
        """Test handling exception with custom message."""
        exc = JobNotFoundError("Custom message")
        http_exc = handle_service_exception(exc)
        
        assert http_exc.detail == "Custom message"

