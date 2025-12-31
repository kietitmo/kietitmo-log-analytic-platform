"""
Custom exceptions for the ingest service.
"""
from fastapi import HTTPException, status


class IngestServiceException(Exception):
    """Base exception for ingest service."""
    pass


class JobNotFoundError(IngestServiceException):
    """Raised when a job is not found."""
    pass


class InvalidJobStateError(IngestServiceException):
    """Raised when a job is in an invalid state for the operation."""
    pass


class StorageError(IngestServiceException):
    """Raised when a storage operation fails."""
    pass


class DatabaseError(IngestServiceException):
    """Raised when a database operation fails."""
    pass


class QueueError(IngestServiceException):
    """Raised when a queue operation fails."""
    pass


class ValidationError(IngestServiceException):
    """Raised when validation fails."""
    pass


def handle_service_exception(exception: IngestServiceException) -> HTTPException:
    """Convert service exceptions to HTTP exceptions."""
    exception_map = {
        JobNotFoundError: (status.HTTP_404_NOT_FOUND, "Job not found"),
        InvalidJobStateError: (status.HTTP_400_BAD_REQUEST, "Invalid job state"),
        StorageError: (status.HTTP_503_SERVICE_UNAVAILABLE, "Storage service unavailable"),
        DatabaseError: (status.HTTP_503_SERVICE_UNAVAILABLE, "Database service unavailable"),
        QueueError: (status.HTTP_503_SERVICE_UNAVAILABLE, "Queue service unavailable"),
        ValidationError: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation error"),
    }
    
    status_code, default_message = exception_map.get(
        type(exception),
        (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")
    )
    
    message = str(exception) if str(exception) else default_message
    return HTTPException(status_code=status_code, detail=message)

