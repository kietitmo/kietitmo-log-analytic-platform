"""
Application constants.
"""
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, Enum):
    """Job type enumeration."""
    FILE_UPLOAD = "FILE_UPLOAD"
    STREAM_INGEST = "STREAM_INGEST"


class LogFormat(str, Enum):
    """Supported log formats."""
    JSON = "json"
    TEXT = "text"
    CSV = "csv"
    NDJSON = "ndjson"


class StorageType(str, Enum):
    """Storage type enumeration."""
    S3 = "s3"
    LOCAL = "local"


# Error messages
ERROR_JOB_NOT_FOUND = "Job not found"
ERROR_INVALID_JOB_STATE = "Invalid job state"
ERROR_FILE_NOT_FOUND = "File not found in storage"
ERROR_DATABASE_CONNECTION = "Database connection error"
ERROR_REDIS_CONNECTION = "Redis connection error"
ERROR_STORAGE_ERROR = "Storage operation failed"

