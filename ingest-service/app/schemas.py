"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class InitUploadRequest(BaseModel):
    """Request schema for initializing file upload."""
    
    filename: str = Field(..., description="Original filename", min_length=1, max_length=255)
    size: int = Field(..., description="File size in bytes", gt=0)
    log_format: str = Field(
        default="json",
        description="Log format (json, text, csv, ndjson)",
    )
    
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


class JobResponse(BaseModel):
    """Basic job response schema."""
    
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress: int = Field(..., description="Job progress percentage", ge=0, le=100)
    
    model_config = {"json_schema_extra": {"example": {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "QUEUED",
        "progress": 0,
    }}}


class JobDetailResponse(BaseModel):
    """Detailed job response schema."""
    
    job_id: str = Field(..., description="Job ID")
    job_type: str = Field(..., description="Job type")
    source: str = Field(..., description="Job source")
    status: str = Field(..., description="Job status")
    progress: int = Field(..., description="Job progress percentage", ge=0, le=100)
    retry_count: int = Field(..., description="Number of retries", ge=0)
    created_at: Optional[datetime] = Field(None, description="Job creation timestamp")
    queued_at: Optional[datetime] = Field(None, description="Job queued timestamp")
    started_at: Optional[datetime] = Field(None, description="Job started timestamp")
    finished_at: Optional[datetime] = Field(None, description="Job finished timestamp")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    
    model_config = {"json_schema_extra": {"example": {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "job_type": "FILE_UPLOAD",
        "source": "api",
        "status": "QUEUED",
        "progress": 0,
        "retry_count": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "queued_at": "2024-01-01T00:00:05Z",
        "started_at": None,
        "finished_at": None,
        "error_message": None,
    }}}
