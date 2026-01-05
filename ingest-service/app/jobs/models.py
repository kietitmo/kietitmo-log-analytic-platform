"""
Database models for the jobs domain.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, TIMESTAMP, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.common.database import Base
from app.common.constants import JobStatus, JobType, StorageType, LogFormat


class Job(Base):
    """Job model for tracking ingestion jobs."""
    
    __tablename__ = "jobs"
    __table_args__ = (
        Index("idx_job_status", "status"),
        Index("idx_job_created_at", "created_at"),
    )

    job_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False)
    status = Column(String, nullable=False, default=JobStatus.CREATED.value, index=True)
    progress = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    queued_at = Column(TIMESTAMP(timezone=True))
    started_at = Column(TIMESTAMP(timezone=True))
    finished_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    error_message = Column(Text)
    
    # Relationship
    file_upload = relationship("FileUpload", back_populates="job", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Job(job_id={self.job_id}, status={self.status}, type={self.job_type})>"


class FileUpload(Base):
    """File upload metadata model."""
    
    __tablename__ = "file_uploads"
    __table_args__ = (
        Index("idx_file_upload_object_key", "object_key"),
    )

    job_id = Column(String, ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True)
    storage_type = Column(String, nullable=False, default=StorageType.S3.value)
    bucket = Column(String, nullable=False)
    object_key = Column(Text, nullable=False)
    local_path = Column(Text)
    file_size = Column(Integer)
    log_format = Column(String, nullable=False, default=LogFormat.JSON.value)
    
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationship
    job = relationship("Job", back_populates="file_upload")

    def __repr__(self) -> str:
        return f"<FileUpload(job_id={self.job_id}, object_key={self.object_key})>"

