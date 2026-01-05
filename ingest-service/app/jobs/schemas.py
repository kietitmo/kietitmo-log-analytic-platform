"""
Pydantic schemas for jobs domain.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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
        "queued_at": "2024-01-01T00:05:00Z",
        "started_at": None,
        "finished_at": None,
        "error_message": None,
    }}}

