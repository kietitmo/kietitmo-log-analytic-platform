"""
Domain exceptions for ingest module.
"""
from app.common.exceptions.domain import DomainException


class IngestDomainException(DomainException):
    """Base domain exception for ingest module."""
    error_code = "INGEST_ERROR"


class UploadNotFoundError(IngestDomainException):
    status_code = 404
    error_code = "UPLOAD_NOT_FOUND"
    message = "Upload not found"


class InvalidUploadStateError(IngestDomainException):
    status_code = 400
    error_code = "INVALID_UPLOAD_STATE"
    message = "Invalid upload state"

