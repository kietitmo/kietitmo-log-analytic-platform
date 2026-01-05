"""
Pydantic schemas for ingest domain.
"""
from pydantic import BaseModel, Field, field_validator


class InitUploadRequest(BaseModel):
    """Request schema for initializing file upload."""
    
    filename: str = Field(..., description="Original filename", min_length=1, max_length=255)
    size: int = Field(..., description="File size in bytes", gt=0, le=100 * 1024 * 1024)  # Max 100MB
    log_format: str = Field(
        default="json",
        description="Log format (json, text, csv, ndjson)",
    )
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate and sanitize filename."""
        # Reject path traversal attempts
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Filename cannot contain path separators or '..'")
        
        # Only allow safe characters: alphanumeric, dash, underscore, dot
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError("Filename contains invalid characters")
        
        return v
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        allowed = {"json", "text", "csv", "ndjson"}
        if v.lower() not in allowed:
            raise ValueError(f"log_format must be one of {allowed}")
        return v.lower()


class InitUploadResponse(BaseModel):
    """Response schema for upload initialization."""
    
    job_id: str = Field(..., description="Job ID")
    presigned_url: str = Field(..., description="Presigned URL for file upload")
    expires_in: int = Field(..., description="URL expiration time in seconds")
    
    model_config = {"json_schema_extra": {"example": {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "presigned_url": "https://s3.example.com/presigned-url",
        "expires_in": 1800,
    }}}


class CompleteUploadRequest(BaseModel):
    """Request schema for completing file upload."""
    
    job_id: str = Field(..., description="Job ID")
    
    model_config = {"json_schema_extra": {"example": {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
    }}}

