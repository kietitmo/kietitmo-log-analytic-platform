"""
Domain exceptions for jobs module.
"""
from app.common.exceptions.domain import DomainException


class JobDomainException(DomainException):
    """Base domain exception for jobs module."""
    error_code = "JOB_ERROR"


class JobNotFoundError(JobDomainException):
    status_code = 404
    error_code = "JOB_NOT_FOUND"
    message = "Job not found"


class InvalidJobStateError(JobDomainException):
    status_code = 400
    error_code = "INVALID_JOB_STATE"
    message = "Invalid job state"

