"""
Upload service for handling file upload operations.
"""
import uuid
from typing import Tuple
from sqlalchemy.orm import Session

from app.jobs.models import Job, FileUpload
from app.common.constants import JobType, JobStatus, StorageType, LogFormat
from app.common.config import settings
from app.common.infrastructure.storage import generate_presigned_put, object_exists
from app.common.infrastructure.queue import enqueue_job
from app.jobs.service import JobService
from app.jobs.exceptions import JobNotFoundError, InvalidJobStateError
from app.common.logger import get_logger
from app.common.exceptions.infrastucture import StorageError

logger = get_logger(__name__)


class UploadService:
    """Service for file upload operations."""
    
    @staticmethod
    def init_upload(
        db: Session,
        filename: str,
        size: int,
        log_format: str = "json",
    ) -> Tuple[Job, FileUpload, str]:
        """
        Initialize a file upload.
        
        Args:
            db: Database session
            filename: Original filename
            size: File size in bytes
            log_format: Log format (json, text, csv, ndjson)
            
        Returns:
            Tuple of (job, file_upload, presigned_url)
        """
        # Validate log format
        log_format_enum = LogFormat.JSON
        try:
            log_format_enum = LogFormat(log_format.lower())
        except ValueError:
            logger.warning(f"Invalid log format '{log_format}', defaulting to JSON")
        
        try:
            # Create job
            job = JobService.create_job(
                db=db,
                job_type=JobType.FILE_UPLOAD,
                source="api",
                status=JobStatus.CREATED,
            )
            
            # Generate object key
            file_extension = filename.split(".")[-1] if "." in filename else "log"
            object_key = f"raw-logs/{job.job_id}.{file_extension}"
            
            # Create file upload metadata
            upload = JobService.create_file_upload(
                db=db,
                job_id=job.job_id,
                bucket=settings.S3_BUCKET,
                object_key=object_key,
                file_size=size,
                log_format=log_format_enum,
                storage_type=StorageType.S3,
            )
            
            # Generate presigned URL
            presigned_url = generate_presigned_put(
                key=object_key,
                expires=settings.S3_PRESIGNED_URL_EXPIRES,
            )

            db.commit()
            return job, upload, presigned_url
        
        except StorageError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            logger.exception("Unexpected error initializing upload")
            raise

    
    @staticmethod
    def complete_upload(db: Session, job_id: str) -> Job:
        """
        Complete a file upload and queue the job for processing.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Updated job instance
            
        Raises:
            JobNotFoundError: If job not found
            InvalidJobStateError: If job is not in CREATED state
            StorageError: If file doesn't exist in storage
        """        
        try:

            # Get job
            job = JobService.get_job_or_raise(db, job_id)
            
            # Validate job state
            JobService.validate_job_state(job, JobStatus.CREATED)
            
            # Get file upload metadata
            upload = JobService.get_file_upload(db, job_id)
            if not upload:
                raise JobNotFoundError(f"File upload metadata not found for job: {job_id}")
            
            # Verify file exists in storage
            if not object_exists(upload.object_key):
                logger.warning(
                    "Uploaded file not found in storage",
                    extra={"object_key": upload.object_key},
                )

                raise StorageError()

            
            # Update job status to QUEUED
            JobService.update_job_status(db, job, JobStatus.QUEUED)
            
            # Enqueue job for processing
            enqueue_job({
                "job_id": job.job_id,
                "job_type": job.job_type,
                "payload": {
                    "bucket": upload.bucket,
                    "key": upload.object_key,
                    "log_format": upload.log_format,
                    "file_size": upload.file_size,
                }
            })
        
        
            db.commit()
            logger.info(f"Completed upload and queued job: job_id={job_id}")
            
            return job
        
        except (JobNotFoundError, InvalidJobStateError, StorageError):
            db.rollback()
            raise

        except Exception:
            db.rollback()
            logger.exception("Unexpected error completing upload")
            raise

